"""Entry point for running the API server."""

import uvicorn


def main() -> None:
    """Run the FastAPI server."""
    uvicorn.run(
        "artifact_search.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
