from fasthtml.common import *
from pathlib import Path
import httpx  # Use httpx for asynchronous requests
import urllib.parse

app, rt = fast_app(live=True)  # live=True for live reloading

upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)

@rt("/")
def get():
    return Titled(
        "File Upload and Link Download Example",
        # File Upload Form
        Form(
            Input(type="file", name="uploaded_file"),
            Button("Upload File", type="submit", cls="primary"),
            hx_post="/upload",
            hx_target="#result-file",  # Unique target for file uploads
        ),
        Div(id="result-file"),

        # Link Download Form
        Form(
            Input(type="text", name="uploaded_link", placeholder="Enter URL"),
            Button("Download from Link", type="submit", cls="primary"),
            hx_post="/linked",
            hx_target="#result-link",  # Unique target for link downloads
        ),
        Div(id="result-link"),
    )

@rt("/upload")
async def post(uploaded_file: UploadFile):
    filename = uploaded_file.filename
    filesize = uploaded_file.size
    filepath = upload_dir / filename

    try:
        with open(filepath, "wb") as f:
            while contents := await uploaded_file.read(1024 * 1024):
                f.write(contents)
        return P(f"File Uploaded: {filename} ({filesize} bytes)")
    except Exception as e:
        return P(f"Error uploading file: {e}")

@rt("/linked")
async def post(uploaded_link: str):  # Correct parameter name
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(uploaded_link, follow_redirects=True) #follow redirects
            response.raise_for_status()  # Raise HTTPStatusError for bad responses (4xx or 5xx)

            # Try to get filename from Content-Disposition header
            if "Content-Disposition" in response.headers:
                header = response.headers["Content-Disposition"]
                filename = header.split("filename=")[-1].strip('"')
            else:
                # Extract filename from URL, handling potential errors.
                path = urllib.parse.urlparse(uploaded_link).path
                filename = Path(path).name
                if not filename:
                    filename = "downloaded_file"

            # Add pdf if not other extension provided
            if not filename.endswith(".pdf") and not "." in filename:
                filename += ".pdf"
                
            filepath = upload_dir / filename

            with open(filepath, "wb") as file:
                async for chunk in response.aiter_bytes():
                    file.write(chunk)

            return P(f"File downloaded from link: {filename}")

    except httpx.RequestError as e:
        return P(f"Request error: {e}")
    except httpx.HTTPStatusError as e:
        return P(f"HTTP error ({e.response.status_code}): {e}")
    except Exception as e:
        return P(f"An unexpected error occurred: {e}")

serve()