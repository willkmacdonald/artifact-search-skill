"""Entry point for running the API server."""

import uvicorn


def main() -> None:
    """Run the FastAPI server."""
    uvicorn.run(
        "artifact_search.api:app",
        host="127.0.0.1",  # localhost only for security
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
