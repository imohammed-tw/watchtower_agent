"""
Export API endpoints
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from database import db
from utils.newsletter_exporter import NewsletterExporter

router = APIRouter()
exporter = NewsletterExporter()


@router.post("/newsletter/{user_id}/latest")
async def export_latest_newsletter(user_id: str, format: str = "html"):
    """Export the latest newsletter to file"""
    try:
        # Get latest newsletter from database
        newsletters = await db.get_user_newsletters(user_id, limit=1)
        if not newsletters:
            raise HTTPException(status_code=404, detail="No newsletters found")

        # For demo, let's create a sample newsletter export
        # In real implementation, you'd fetch the full newsletter content

        if format.lower() == "html":
            # Create a sample HTML file
            filename = f"newsletter-{user_id}-latest.html"
            filepath = os.path.join("exports", filename)

            sample_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Watchtower Newsletter</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; }}
        a {{ color: #3498db; }}
    </style>
</head>
<body>
    <h1>AI Watchtower Newsletter</h1>
    <p>Generated for user: {user_id}</p>
    <p>This is a sample export. The actual newsletter content would be rendered here with proper formatting and hyperlinks.</p>
    
    <h2>Executive Highlights</h2>
    <p>Your personalized AI governance and compliance insights would appear here...</p>
    
    <h2>Technical Breakthroughs</h2>
    <p>Latest AI technology developments...</p>
    
    <p><em>Export generated on: {newsletters[0]['generated_at']}</em></p>
</body>
</html>"""

            os.makedirs("exports", exist_ok=True)
            with open(filepath, "w") as f:
                f.write(sample_html)

            return FileResponse(filepath, filename=filename, media_type="text/html")

        else:
            raise HTTPException(
                status_code=400, detail="Unsupported format. Use 'html' or 'markdown'"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
