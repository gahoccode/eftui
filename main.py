"""CLI entrypoint for the VietFrontier terminal explorer."""

from vietfrontier.bootstrap import build_application


def main() -> None:
    """Launch the interactive portfolio optimization TUI."""
    app = build_application()
    app.run()


if __name__ == "__main__":
    main()
