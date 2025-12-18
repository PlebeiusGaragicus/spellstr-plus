import os
import json
import secrets
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("spellstr")
logging.getLogger("aiosqlite").setLevel(logging.WARNING)
logger.info(f"Starting Spellstr API with log level: {log_level}")

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

# Admin configuration
ADMIN_NPUB = os.getenv("ADMIN_NPUB", "")
logger.info(f"Admin npub configured: {ADMIN_NPUB[:20]}..." if ADMIN_NPUB else "No admin npub configured")


def verify_admin(x_npub: Optional[str] = None) -> bool:
    """Verify that the request is from an admin"""
    if not ADMIN_NPUB:
        logger.warning("No ADMIN_NPUB configured - admin access denied")
        return False
    if not x_npub:
        logger.warning("No x-npub header provided")
        return False
    is_admin = x_npub == ADMIN_NPUB
    logger.debug(f"Admin verification: provided={x_npub[:20]}..., expected={ADMIN_NPUB[:20]}..., match={is_admin}")
    return is_admin


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
    Redeem a Cashu token using the cashu library.
    Returns (success, amount, message)
    """
    logger.debug(f"=== TOKEN REDEMPTION START ===")
    logger.debug(f"Token received (first 50 chars): {token[:50] if len(token) > 50 else token}...")
    logger.debug(f"Token length: {len(token)}")
    
    mint_url = os.getenv("MINT_URL", "https://mint.minibits.cash/Bitcoin")
    wallet_db = os.getenv("WALLET_DB", "./wallet_db")
    logger.debug(f"MINT_URL: {mint_url}")
    logger.debug(f"WALLET_DB: {wallet_db}")
    
    try:
        logger.debug("Attempting to import cashu library...")
        from cashu.wallet.wallet import Wallet
        from cashu.core.base import TokenV4
        logger.debug("Successfully imported Wallet and TokenV4 from cashu")
        
        logger.debug("Deserializing token...")
        try:
            token_obj = TokenV4.deserialize(token)
            logger.debug(f"Token deserialized successfully")
            logger.debug(f"Token mint: {token_obj.mint}")
            logger.debug(f"Token has {len(token_obj.proofs)} proofs")
        except Exception as e:
            logger.error(f"Failed to deserialize token: {e}")
            return False, 0, f"Invalid token format: {str(e)}"
        
        token_mint_url = token_obj.mint
        logger.debug(f"Using mint URL from token: {token_mint_url}")
        
        logger.debug(f"Creating wallet with mint URL: {token_mint_url}")
        wallet = await Wallet.with_db(
            url=token_mint_url,
            db=wallet_db,
        )
        logger.debug("Wallet instance created successfully")
        
        logger.debug("Loading mint info...")
        await wallet.load_mint()
        logger.debug("Mint loaded successfully")
        
        # Get proofs from token
        proofs = token_obj.proofs
        input_amount = sum(p.amount for p in proofs)
        logger.debug(f"Input proofs total amount: {input_amount} sats")
        logger.debug(f"Number of proofs: {len(proofs)}")
        
        for i, p in enumerate(proofs):
            logger.debug(f"  Proof {i}: amount={p.amount}, has_dleq={p.dleq is not None}")
        
        logger.debug(f"Attempting to swap proofs at mint (split with amount=0)...")
        
        # Use split directly to swap proofs - this avoids DLEQ verification
        # which may fail if the token doesn't include DLEQ proofs
        keep_proofs, send_proofs = await wallet.split(proofs=proofs, amount=0)
        logger.debug(f"Split result: keep={len(keep_proofs)}, send={len(send_proofs)}")
        
        # The proofs are now in our wallet
        total_amount = sum(p.amount for p in keep_proofs) if keep_proofs else input_amount
        logger.info(f"TOKEN REDEEMED SUCCESSFULLY: {total_amount} sats")
        logger.debug(f"=== TOKEN REDEMPTION END (SUCCESS) ===")
        
        return True, total_amount, f"Redeemed {total_amount} sats"
        
    except ImportError as e:
        logger.error(f"IMPORT ERROR: cashu library not available: {e}")
        logger.debug(f"=== TOKEN REDEMPTION END (IMPORT ERROR) ===")
        return False, 0, f"Cashu library not installed: {str(e)}"
        
    except Exception as e:
        logger.error(f"REDEMPTION FAILED: {type(e).__name__}: {str(e)}")
        logger.exception("Full traceback:")
        logger.debug(f"=== TOKEN REDEMPTION END (ERROR) ===")
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
    logger.info(f"POST /api/redeem - pubkey: {request.pubkey}")
    logger.debug(f"Request body: token={request.token[:30] if request.token else 'None'}...")
    
    if not request.token:
        logger.warning("Redeem request missing token")
        raise HTTPException(status_code=400, detail="Token is required")
    
    success, amount, message = await redeem_cashu_token(request.token)
    
    logger.info(f"Redeem result: success={success}, amount={amount}, message={message}")
    
    return RedeemResponse(
        success=success,
        amount=amount,
        message=message
    )


@app.post("/api/session/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest):
    """Start a spelling session after payment verification"""
    logger.info(f"POST /api/session/start - pubkey: {request.pubkey}")
    logger.debug(f"Token provided: {bool(request.token)}")
    if request.token:
        logger.debug(f"Token (first 30 chars): {request.token[:30]}...")
    
    if request.token:
        logger.info("Processing payment token...")
        success, amount, message = await redeem_cashu_token(request.token)
        logger.info(f"Payment result: success={success}, amount={amount}")
        
        if not success:
            logger.warning(f"Payment failed: {message}")
            return SessionResponse(
                success=False,
                message=f"Payment failed: {message}"
            )
        if amount < SESSION_COST_SATS:
            logger.warning(f"Insufficient payment: {amount} < {SESSION_COST_SATS}")
            return SessionResponse(
                success=False,
                message=f"Insufficient payment. Required: {SESSION_COST_SATS} sat, received: {amount} sats"
            )
        logger.info(f"Payment verified: {amount} sats received")
    else:
        logger.warning("No token provided - session started without payment")
    
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS)
    
    sessions[session_id] = {
        "pubkey": request.pubkey,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    
    logger.info(f"Session created: {session_id[:16]}... expires at {expires_at.isoformat()}")
    logger.debug(f"Active sessions count: {len(sessions)}")
    
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


# =============================================================================
# Admin Endpoints
# =============================================================================

@app.post("/admin/verify")
async def admin_verify(x_npub: Optional[str] = Header(None)):
    """Verify admin access"""
    logger.info(f"POST /admin/verify - npub: {x_npub[:20] if x_npub else 'None'}...")
    
    if not verify_admin(x_npub):
        raise HTTPException(status_code=403, detail="Unauthorized - not an admin")
    
    return {"success": True, "message": "Admin verified"}


@app.get("/admin/stats")
async def admin_stats(x_npub: Optional[str] = Header(None)):
    """Get wallet stats for admin dashboard"""
    logger.info(f"GET /admin/stats")
    
    if not verify_admin(x_npub):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    mint_url = os.getenv("MINT_URL", "https://mint.minibits.cash/Bitcoin")
    wallet_db = os.getenv("WALLET_DB", "./wallet_db")
    
    wallet_balance = 0
    proof_count = 0
    
    try:
        from cashu.wallet.wallet import Wallet
        
        wallet = await Wallet.with_db(url=mint_url, db=wallet_db, unit="sat")
        await wallet.load_mint()
        await wallet.load_proofs(reload=True)
        
        # available_balance returns an object with .amount property
        wallet_balance = wallet.available_balance.amount if hasattr(wallet.available_balance, 'amount') else int(wallet.available_balance)
        proof_count = len(wallet.proofs) if hasattr(wallet, 'proofs') else 0
        logger.debug(f"Wallet balance: {wallet_balance}, proofs: {proof_count}")
    except Exception as e:
        logger.error(f"Failed to get wallet stats: {e}")
        logger.exception("Full traceback:")
    
    return {
        "wallet_balance": wallet_balance,
        "sessions_count": len(sessions),
        "proof_count": proof_count,
        "default_mint": mint_url,
        "wallet_db": wallet_db,
    }


@app.get("/admin/proofs")
async def admin_proofs(x_npub: Optional[str] = Header(None)):
    """Get list of proofs in wallet"""
    logger.info(f"GET /admin/proofs")
    
    if not verify_admin(x_npub):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    mint_url = os.getenv("MINT_URL", "https://mint.minibits.cash/Bitcoin")
    wallet_db = os.getenv("WALLET_DB", "./wallet_db")
    
    proofs_list = []
    
    try:
        from cashu.wallet.wallet import Wallet
        
        wallet = await Wallet.with_db(url=mint_url, db=wallet_db, unit="sat")
        await wallet.load_mint()
        await wallet.load_proofs(reload=True)
        
        if hasattr(wallet, 'proofs') and wallet.proofs:
            for p in wallet.proofs:
                proofs_list.append({
                    "amount": p.amount,
                    "keyset_id": p.id[:16] if p.id else "unknown",
                })
    except Exception as e:
        logger.error(f"Failed to get proofs: {e}")
        logger.exception("Full traceback:")
    
    return {
        "count": len(proofs_list),
        "proofs": proofs_list,
    }


@app.post("/admin/sweep")
async def admin_sweep(x_npub: Optional[str] = Header(None)):
    """Sweep all wallet balance to a cashu token"""
    logger.info(f"POST /admin/sweep")
    
    if not verify_admin(x_npub):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    mint_url = os.getenv("MINT_URL", "https://mint.minibits.cash/Bitcoin")
    wallet_db = os.getenv("WALLET_DB", "./wallet_db")
    
    try:
        from cashu.wallet.wallet import Wallet
        
        wallet = await Wallet.with_db(url=mint_url, db=wallet_db, unit="sat")
        await wallet.load_mint()
        await wallet.load_proofs(reload=True)
        
        # available_balance returns an object with .amount property
        balance = wallet.available_balance.amount if hasattr(wallet.available_balance, 'amount') else int(wallet.available_balance)
        
        if balance < 1:
            return {"success": False, "error": "No balance to sweep"}
        
        proofs = wallet.proofs
        if not proofs:
            return {"success": False, "error": "No proofs in wallet"}
        
        logger.info(f"Sweeping {balance} sats to token...")
        
        # Use wallet's built-in serialization method directly on existing proofs
        token = await wallet.serialize_proofs(proofs, memo="Spellstr wallet sweep")
        
        logger.info(f"Sweep successful: {balance} sats")
        logger.debug(f"Token: {token[:50]}...")
        
        # Invalidate proofs after creating token (remove from wallet)
        await wallet.invalidate(proofs=proofs, check_spendable=False)
        
        return {
            "success": True,
            "amount": balance,
            "token": token,
        }
        
    except Exception as e:
        logger.error(f"Sweep failed: {e}")
        logger.exception("Full traceback:")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
