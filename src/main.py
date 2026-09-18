import argparse
import logging
import os

from bronze.bronze import run_bronze_layer
from generator.generate_data import main as run_generator
from gold.gold import run_gold_layer
from silver.silver import run_silver_layer

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure application-wide logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the banking data pipeline.",
    )

    parser.add_argument(
        "--stage",
        required=True,
        choices=(
            "generator",
            "bronze",
            "silver",
            "gold",
            "full",
        ),
        help="Pipeline stage to execute.",
    )

    return parser.parse_args()


def run_stage(stage: str) -> None:
    """Run the requested pipeline stage."""
    if stage == "generator":
        logger.info("Running Generator stage.")
        run_generator()
        return

    if stage == "bronze":
        logger.info("Running Bronze stage.")
        run_bronze_layer()
        return

    if stage == "silver":
        logger.info("Running Silver stage.")
        run_silver_layer()
        return

    if stage == "gold":
        logger.info("Running Gold stage.")
        run_gold_layer()
        return

    if stage == "full":
        logger.info("Running full pipeline.")

        logger.info("Step 1/4 - Generator.")
        run_generator()

        logger.info("Step 2/4 - Bronze.")
        run_bronze_layer()

        logger.info("Step 3/4 - Silver.")
        run_silver_layer()

        logger.info("Step 4/4 - Gold.")
        run_gold_layer()

        logger.info("Full pipeline completed successfully.")
        return

    raise ValueError(f"Unsupported pipeline stage: {stage}")


def main() -> int:
    """Run the requested pipeline stage."""
    configure_logging()

    args = parse_arguments()

    try:
        run_stage(args.stage)
    except Exception:
        logger.exception(
            "Pipeline execution failed | stage=%s",
            args.stage,
        )
        return 1

    logger.info(
        "Pipeline stage completed successfully | stage=%s",
        args.stage,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())