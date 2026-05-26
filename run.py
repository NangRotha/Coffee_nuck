import uvicorn
import os

if __name__ == "__main__":
    # Make sure upload directories exist
    os.makedirs("app/uploads/products", exist_ok=True)
    os.makedirs("app/uploads/staff", exist_ok=True)
    os.makedirs("app/uploads/events", exist_ok=True)
    os.makedirs("app/uploads/gallery", exist_ok=True)
    os.makedirs("app/uploads/settings", exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )