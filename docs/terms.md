# Cashu terminology

## **Mint (verb) / Minting**
**Meaning:** Convert a paid Lightning invoice into ecash proofs (tokens) issued by a specific mint.

**Flow:**
- You request a **mint quote / invoice** from a mint.
- Someone pays that invoice.
- You call **`mint`** to receive newly issued ecash proofs.

**Key point:** Minting creates ecash **from Lightning → ecash**. It does *not* “move ecash to another mint” by itself.

## **Melt / Melting**
**Meaning:** Spend ecash proofs at a mint so the mint pays a Lightning invoice for you (i.e., “withdraw to Lightning”).

**Flow:**
- You obtain a BOLT11 invoice you want paid.
- You request a **melt quote** (fees, etc.).
- You submit proofs + invoice to **melt**.
- The mint pays the invoice using its Lightning backend.

**Key point:** Melting converts **ecash → Lightning**.


## **Send (wallet-to-wallet transfer)**
**Meaning:** Package up some of your proofs into a token string (e.g. `cashuB...`) and give it to someone else.

**Flow:**
- Your wallet selects/splits proofs and serializes them into a token string.
- The recipient “receives”/redeems it.

**Key point:** Sending is **ecash → ecash**, and typically stays tied to the **same mint** that issued those proofs.

## **Receive / Redeem**
These are often conflated.

- **Receive (UX term):** “Accept this token string.”
- **Redeem (protocol reality):** The recipient wallet contacts the mint to **swap/redeem** the received proofs into fresh proofs under the recipient’s control, and marks old ones as spent.

In this repo, the helper [receive()](cci:1://file:///Users/myca/Downloads/2026/nutshell/cashu/wallet/helpers.py:101:0-109:22) ends up calling redeem logic ([redeem_universal()](cci:1://file:///Users/myca/Downloads/2026/nutshell/cashu/wallet/helpers.py:77:0-82:41) → `wallet.redeem(...)`).

**Key point:** Proper receiving is not just “store the string”—it’s a mint-interaction to prevent double-spends.

## **Swap / Split**
**Meaning:** Rearrange proofs into different denominations and/or refresh them (and possibly attach conditions like P2PK/HTLC).

**Typical uses:**
- Make change.
- Prepare exact amounts to send.
- Refresh proofs.

This is internal “ecash housekeeping” and is not Lightning.

## 1) **Withdraw to Lightning = Melt**
This is a true “withdrawal” from ecash into Lightning.  
You end up with sats in a Lightning wallet/service (custodial or your own node—your choice).

## 2) **“Mint them into tokens to be redeemed in another wallet”**
This is **not** how moving existing ecash works.

- **Minting** requires paying Lightning to the mint. It creates *new* ecash.
- If you already have ecash and want another wallet to have it, you normally **send** a token string (ecash → ecash), not “mint”.

So the second option is really either:

### **Option A: Send ecash tokens to another wallet (same mint)**
- Your backend serializes proofs into a `cashu...` token.
- Your other wallet receives/redeems it.
- Funds remain **claims on the same mint** (same issuer), just moved to a different holder.

This is the closest analog to “withdraw to another wallet” without touching Lightning.

### **Option B: Move value from Mint X to Mint Y (cross-mint)**
There is **no direct ecash-to-ecash bridge between mints** in the protocol. To end up with ecash from a different mint, you typically do:

- **Melt at Mint X** (ecash → Lightning), paying an invoice that results in value you control
- **Mint at Mint Y** (Lightning → ecash), by paying Mint Y’s invoice

So cross-mint migration is basically: **melt + mint**, with Lightning in the middle.

---

# Practical summary in one sentence
- **Melt**: ecash → Lightning (a true withdrawal).
- **Send/Receive**: ecash → ecash (transfer to another wallet; same mint).
- **Change mints**: you usually must **melt on mint A and mint on mint B** (Lightning as the bridge).

---

# Status
- **Completed**: Explained the terminology and corrected the “mint into another mint” interpretation, including the right mental model for same-mint transfers vs cross-mint moves.





# Can you receive ecash if you’re *not* running a mint?

Yes. A Cashu **wallet-only** application can absolutely receive ecash.

But “receive” has two levels:

## 1) “Receive” as in *accept a token string*
A user can give you a Cashu token string (`cashuB...` / `cashuA...`). Your backend can parse it offline (no mint needed) into proofs.

In this repo that’s basically:
- [deserialize_token_from_string(token_str)](cci:1://file:///Users/myca/Downloads/2026/nutshell/cashu/wallet/helpers.py:85:0-98:36) in [cashu/wallet/helpers.py](cci:7://file:///Users/myca/Downloads/2026/nutshell/cashu/wallet/helpers.py:0:0-0:0)

**However:** at this stage you’ve only parsed data. You have **not** made it safe.

---

## 2) “Receive safely” (prevent double-spend) = **Redeem with the mint**
To prevent double-spending, you generally must **talk to the mint that issued the proofs**.

Why: ecash tokens are **bearer**. A malicious user can hand the *same* token string to you and someone else. The only authoritative source that can tell “spent vs unspent” is the **issuing mint’s ledger**.

So the safe flow is:

- **Step A: Parse the token** and identify which mint it belongs to  
  - TokenV4 includes the mint URL (`m=`). TokenV3 can include multiple mints.
- **Step B: Create/use a `Wallet` instance pointed at that mint URL**
- **Step C: Call redeem** (this library does it via [receive()](cci:1://file:///Users/myca/Downloads/2026/nutshell/cashu/wallet/helpers.py:101:0-109:22) → [redeem_universal()](cci:1://file:///Users/myca/Downloads/2026/nutshell/cashu/wallet/helpers.py:77:0-82:41) → `wallet.redeem(...)`)  
  - Redeeming effectively swaps those incoming proofs for **fresh proofs** controlled by your wallet DB, and the mint marks the originals as spent.

That mint interaction is exactly what makes it non-double-spendable *for you*.

---

# Does the library need to speak to the user’s mint?

## If you want strong guarantees: **Yes**
To actually credit a user’s account safely, your backend must confirm with the mint (via redeem/swap/check-state style calls) because:

- Offline you cannot know if proofs were already spent elsewhere.
- Even if proofs include DLEQ or other data, that does not replace the mint’s spent-state.

**Rule of thumb:**  
- **Don’t credit balances** until you have successfully redeemed (or at least checked state and then redeemed).

## Can you do it “offline-only”?
Only with weaker semantics, for example:
- You accept tokens but treat them as “pending/unconfirmed”
- You only finalize later when you can contact the mint and redeem
- Or you accept them with explicit risk (“may be double-spent”)

That’s usually not acceptable for “paid users” on a website.

---

# What “mint” do you need if you aren’t running one?

You don’t run a mint yourself, but you still rely on **some external mint(s)** that issue the ecash you accept.

So your backend wallet will:
- receive token
- read the mint URL embedded in it (or provided by the user / discovered from keyset DB)
- contact that mint over HTTPS to redeem

---

# Practical backend model (minimal + safe)

- **Endpoint** `POST /payments/cashu` with body `{ token: "cashuB..." }`
- Server:
  - parse token
  - instantiate `Wallet` for that mint URL (and your backend’s wallet DB)
  - call redeem/receive (mint interaction)
  - if it succeeds, **credit user**
  - if it fails, reject and do not credit
