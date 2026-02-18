from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mpesa import initiate_stk_push
import os
from fastapi.responses import HTMLResponse
from pathlib import Path

INDEX_HTML = Path("index.html").read_text()

app = FastAPI(title="Voltex Technology - Pool Payment Backend")

# CORS (for local dev – tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # ← change to your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (your frontend: index.html, css, js)
app.mount("/statics", StaticFiles(directory="statics"), name="statics")

class PaymentRequest(BaseModel):
    phone: str
    amount: int
    games: int
    tableId: str

# Serve frontend at root
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return INDEX_HTML
# Payment initiation – called by script.js
@app.post("/api/initiate-stk")
async def initiate_payment(req: PaymentRequest):
    print(f"Received payment request:")
    print(f"  Phone   : {req.phone}")
    print(f"  Amount  : {req.amount} KSh")
    print(f"  Games   : {req.games}")
    print(f"  Table   : {req.tableId}")

    try:
        # Normalize phone (Daraja wants 2547xxxxxxxx without +)
        phone_clean = req.phone.replace("+", "").replace(" ", "")
        if phone_clean.startswith("0"):
            phone_clean = "254" + phone_clean[1:]

        response = await initiate_stk_push(
            phone=phone_clean,
            amount=req.amount,
            account_reference=f"POOL-{req.tableId}",
            transaction_desc=f"{req.games} game(s) on {req.tableId}"
        )

        if response.get("ResponseCode") == "0":
            return {
                "success": True,
                "message": "STK Push sent – check phone for prompt",
                "checkout_request_id": response.get("CheckoutRequestID"),
                "tableId": req.tableId
            }
        else:
            raise HTTPException(status_code=400, detail=response.get("ResponseDescription", "STK failed"))

    except Exception as e:
        print(f"Error initiating STK: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Daraja callback (must be public HTTPS URL)
@app.post("/api/mpesa/callback")
async def mpesa_callback(request: Request):
    try:
        payload = await request.json()
        body = payload.get("Body", {}).get("stkCallback", {})

        checkout_id = body.get("CheckoutRequestID")
        result_code = body.get("ResultCode")
        result_desc = body.get("ResultDesc")

        print(f"Callback received:")
        print(f"  CheckoutID: {checkout_id}")
        print(f"  ResultCode: {result_code}")
        print(f"  ResultDesc: {result_desc}")

        if result_code == 0:
            # Payment SUCCESS → notify the table's ESP here
            # Example: requests.get(f"http://192.168.x.x/unlock?games=3")
            # You need tableId → ESP IP mapping (database later)
            print("→ Payment SUCCESS – unlock table!")
        else:
            print("→ Payment FAILED")

        return {"status": "Callback processed"}

    except Exception as e:
        print(f"Callback error: {str(e)}")
        return JSONResponse({"status": "error"}, status_code=400)

# Optional: health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}