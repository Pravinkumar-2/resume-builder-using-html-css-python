import os
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI()

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Paths
USERS_DB = "users.csv"
RESUMES_DB = "resumes.csv"

# Initialize databases
if not os.path.exists(USERS_DB):
    pd.DataFrame(columns=["name", "email", "password"]).to_csv(USERS_DB, index=False)

if not os.path.exists(RESUMES_DB):
    pd.DataFrame(columns=["id", "user_email", "theme_color", "content_json"]).to_csv(RESUMES_DB, index=False)

# Pydantic models for request bodies
class RegisterUser(BaseModel):
    name: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

class ResumeUpdate(BaseModel):
    theme_color: str
    content_json: Dict[str, Any]

# Auth Endpoints
@app.post("/auth/register")
def register(user: RegisterUser):
    df = pd.read_csv(USERS_DB)
    if user.email in df["email"].values:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = pd.DataFrame([{
        "name": user.name,
        "email": user.email,
        "password": user.password
    }])
    
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USERS_DB, index=False)
    
    return {"message": "Registration successful"}

@app.post("/auth/login")
def login(user: LoginUser):
    df = pd.read_csv(USERS_DB)
    user_record = df[(df["email"] == user.email) & (df["password"] == user.password)]
    
    if user_record.empty:
        raise HTTPException(status_code=401, detail="Invalid credential")
    
    return {"access_token": f"fake-jwt-token-{user.email}"}

# Resumes Endpoints
@app.put("/resumes/{rid}")
def save_resume(rid: str, update: ResumeUpdate):
    # Retrieve email from fake token or simply store by rid.
    # The frontend simulates by just saving it.
    df = pd.read_csv(RESUMES_DB)
    import json
    
    content_str = json.dumps(update.content_json)
    
    if rid in df["id"].values:
        # Update existing
        df.loc[df["id"] == rid, "theme_color"] = update.theme_color
        df.loc[df["id"] == rid, "content_json"] = content_str
    else:
        # Insert new
        new_resume = pd.DataFrame([{
            "id": rid,
            "user_email": "unknown@email.com", # Mocking without real auth validation
            "theme_color": update.theme_color,
            "content_json": content_str
        }])
        df = pd.concat([df, new_resume], ignore_index=True)
        
    df.to_csv(RESUMES_DB, index=False)
    return {"message": "Saved successfully"}

@app.delete("/resumes/{rid}")
def delete_resume(rid: str):
    df = pd.read_csv(RESUMES_DB)
    if rid not in df["id"].values:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    df = df[df["id"] != rid]
    df.to_csv(RESUMES_DB, index=False)
    return {"message": "Deleted successfully"}

@app.get("/resumes/{rid}/download")
def download_resume(rid: str):
    # This intentionally returns 404 to trigger frontend JS window.print() fallback.
    raise HTTPException(status_code=404, detail="Backend PDF generation disabled. Fallback to print.")

# Serve static frontend files on the root directory
# Placed at the end to not override API endpoints
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
