from loguru import logger

from src.guards.sanitizer import OutputSanitizer
from src.guards.validator import InputValidator
from src.schemas.pipeline import ClassifyResult, GatherResult, PipelineState, Stage
from src.services.analyzer import DataAnalyzer
from src.services.gatherer import DataGatherer
from src.services.memory_service import MemoryService
from src.utils.report_formatter import ReportFormatter


class ReportService:
    def __init__(
        self,
        gatherer: DataGatherer,
        memory: MemoryService,
        analyzer: DataAnalyzer,
        formatter: ReportFormatter,
    ) -> None:
        self._gatherer = gatherer
        self._memory = memory
        self._analyzer = analyzer
        self._formatter = formatter

    async def business_report(self, time_range: str, user_id: str) -> str:
        state = PipelineState()

        user_ctx = await self._memory.get_user_context(user_id)
        spec = ClassifyResult(
            report_type="business",
            time_range=user_ctx.preferred_time_range if time_range == "this_month" else time_range,
            user_id=user_id,
            language=user_ctx.preferred_language,
            output_format=user_ctx.preferred_format,
        )
        since_date = InputValidator.time_range_to_date(spec.time_range)
        state.transition(Stage.GATHER)
        logger.info(f"Pipeline: {state.history[-1].name} → {state.current.name}")

        data = await self._gatherer.gather(spec, since_date)
        state.transition(Stage.ANALYZE)

        previous = await self._memory.get_previous_metrics(user_id, "business")
        analysis = await self._analyzer.analyze(spec, data, self._memory, previous)

        if analysis.needs_regather and state.can_retry:
            state.retries += 1
            logger.info(f"[FEEDBACK] Re-gathering: {analysis.regather_sources}")
            state.transition(Stage.GATHER)
            data = await self._gatherer.gather(spec, since_date)
            state.transition(Stage.ANALYZE)
            analysis = await self._analyzer.analyze(spec, data, self._memory, previous)

        state.transition(Stage.FORMAT)
        report = self._formatter.format(spec, data, analysis)

        report, injections = OutputSanitizer.clean(report)
        if injections:
            logger.warning(f"Prompt injection detected: {injections}")
            report += "\n\nWARNING: Some data may contain suspicious content."

        state.transition(Stage.DONE)

        metrics = self._extract_metrics(data)
        await self._memory.record_report(user_id, "business", time_range, metrics)
        if data.has_data and data.sales_summary:
            await self._memory.update_baselines(
                data.sales_summary.total_revenue, data.sales_summary.total_sales
            )

        logger.info(f"Pipeline: stages={[stage.name for stage in state.history]} retries={state.retries}")
        return report

    @staticmethod
    def _extract_metrics(data: GatherResult) -> dict[str, float | int]:
        metrics: dict[str, float | int] = {}
        if data.sales_summary:
            metrics["total_revenue"] = data.sales_summary.total_revenue
            metrics["total_sales"] = data.sales_summary.total_sales
            metrics["avg_ticket"] = data.sales_summary.avg_ticket
        return metrics
