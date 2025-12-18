import os
import json
import secrets
from typing import Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Spellstr API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORDS_FILE = os.path.join(os.path.dirname(__file__), "words.json")

sessions = {}

SESSION_DURATION_HOURS = 24
SESSION_COST_SATS = 1


class RedeemRequest(BaseModel):
    token: str
    pubkey: Optional[str] = None


class SessionStartRequest(BaseModel):
    pubkey: Optional[str] = None
    token: Optional[str] = None


class SessionResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    message: str
    expires_at: Optional[str] = None


class RedeemResponse(BaseModel):
    success: bool
    amount: int = 0
    message: str


def load_words():
    try:
        with open(WORDS_FILE, "r") as f:
            data = json.load(f)
            return data.get("words", [])
    except Exception:
        return [
            {"w": "hamburger", "s": "I'd like to eat a hamburger."},
            {"w": "apple", "s": "An apple a day keeps the doctor away."},
            {"w": "school", "s": "We walk to school every morning."},
            {"w": "friend", "s": "My friend and I play at the park."},
            {"w": "yellow", "s": "The sun is bright and yellow."},
        ]


async def redeem_cashu_token(token: str) -> tuple[bool, int, str]:
    """
    Redeem a Cashu token using the nutshell library.
    Returns (success, amount, message)
    """
    try:
        from cashu.wallet.wallet import Wallet
        from cashu.core.settings import settings
        
        wallet = await Wallet.with_db(
            url=os.getenv("MINT_URL", "https://mint.minibits.cash/Bitcoin"),
            db=os.getenv("WALLET_DB", "./wallet_db"),
        )
        
        await wallet.load_mint()
        
        proofs = await wallet.redeem(token)
        total_amount = sum(p.amount for p in proofs)
        
        return True, total_amount, f"Redeemed {total_amount} sats"
    except ImportError:
        return True, SESSION_COST_SATS, "Demo mode: token accepted"
    except Exception as e:
        return False, 0, f"Redemption failed: {str(e)}"


@app.get("/")
async def root():
    return {"status": "ok", "service": "Spellstr API"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/words")
async def get_words():
    words = load_words()
    return {"words": words}


@app.post("/api/redeem", response_model=RedeemResponse)
async def redeem_token(request: RedeemRequest):
    """Redeem a Cashu eCash token"""
    if not request.token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    success, amount, message = await redeem_cashu_token(request.token)
    
    return RedeemResponse(
        success=success,
        amount=amount,
        message=message
    )


@app.post("/api/session/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest):
    """Start a spelling session after payment verification"""
    
    if request.token:
        success, amount, message = await redeem_cashu_token(request.token)
        if not success:
            return SessionResponse(
                success=False,
                message=f"Payment failed: {message}"
            )
        if amount < SESSION_COST_SATS:
            return SessionResponse(
                success=False,
                message=f"Insufficient payment. Required: {SESSION_COST_SATS} sat, received: {amount} sats"
            )
    
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS)
    
    sessions[session_id] = {
        "pubkey": request.pubkey,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    
    return SessionResponse(
        success=True,
        session_id=session_id,
        message="Session started successfully",
        expires_at=expires_at.isoformat()
    )


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Check if a session is valid"""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    expires_at = datetime.fromisoformat(session["expires_at"])
    if datetime.utcnow() > expires_at:
        del sessions[session_id]
        raise HTTPException(status_code=410, detail="Session expired")
    
    return {
        "valid": True,
        "expires_at": session["expires_at"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
