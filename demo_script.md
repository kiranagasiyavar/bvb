# AnticipateCart: 3-Minute Hackathon Demo Script
**Rezolve Labs Challenge 1: Anticipatory Commerce**

---

### Timing Breakdown
- **0:00 - 0:45**: Problem & Anticipatory Typed Search Demo (Part A Core)
- **0:45 - 1:30**: Mid-Stream Corrections & Code-Mixed Hindi Demo
- **1:30 - 2:15**: Accessibility Voice-First Shopping Demo (Part B)
- **2:15 - 3:00**: Live Restock Notification & Admin Inventory Update Demo

---

### ACT 1: Typed Anticipatory Search (0:00 - 0:45)
**Presenter**:
> *"Judges, traditional e-commerce makes shoppers type out complete sentences and hit enter before seeing what they want. AnticipateCart finds the exact product before you even finish typing."*

**Action**:
1. Open `http://127.0.0.1:8000`. Show the unique Cyber-Luxe interface featuring the Cognition Radar HUD, 5-bar audio visualizer equalizer, and real-time Confidence Telemetry.
2. Click the quick button **"▶ 1. Early Commit (Pacevo)"** (or type: `Pacevo navy casual sneakers size 9 UK for a wedding`).
3. Point to the screen as tokens arrive word-by-word:
   - At word 1 (`Pacevo`): Brand extracted with 98% confidence.
   - At word 4 (`sneakers`): Category resolved to `sneakers`, confidence jumps to 68%.
   - At word 7 (`9 UK`): Size locked in. Score gap is decisive and trailing phrase starts (`for a wedding`).
   - The HUD pulses neon cyan: **`🎯 COMMITTED! Pacevo Navy Casual Sneakers (UK 9)`**.
   - Notice: Committed **3 full words before the shopper finished speaking/typing**! Zero wrong commits!

---

### ACT 2: Mid-Stream Correction & Hindi-English Code-Mix (0:45 - 1:30)
**Presenter**:
> *"Shoppers change their minds mid-sentence. Watch how AnticipateCart handles mid-stream retractions and Hindi-English code mixing."*

**Action 1 (Mid-Stream Correction)**:
1. Click **"▶ 2. Mid-Stream Correction"** (`Kudova green runners size 6 wait I meant size 8 as a gift`).
2. Show the alert pill appearing:
   - **`⚠️ Mid-Stream Correction: Retracted size='6' -> Overridden to '8'`**.
   - The engine automatically purges the stale size 6 hypothesis, runs verification search, and commits to the size 8 Kudova running shoes without resetting the session!

**Action 2 (Code-Mixed Query)**:
1. Click **"▶ 4. Hindi-English Code-Mix"** (`mujhe Loomsy navy casual shoes nau number chahiye 4500 tak`).
2. Show the prediction dashboard:
   - Extracted `colour = navy`.
   - Extracted `size = 9` from *nau number*.
   - Extracted `budget = ₹4500` from *4500 tak*.
   - Top matching Loomsy Navy Casual Shoes displayed instantly!

---

### ACT 3: Accessibility Voice-First Shopping with Female Voice (1:30 - 2:15)
**Presenter**:
> *"For millions of blind, elderly, and motor-impaired individuals, visual search bars are inaccessible. Let's switch to AnticipateCart's Accessibility Persona."*

**Action**:
1. Click the User Switcher button in the navbar: **"👤 Standard User"** -> switches to **"♿ Accessibility Voice User"**.
2. Notice the UI transforms into WCAG AAA High Contrast mode (lumina black background, high-contrast cyan/amber borders, enlarged text).
3. The system automatically speaks aloud in a **clear, natural female voice** (`Microsoft Zira` / `Google UK English Female` / `Samantha`):
   > *"Welcome to AnticipateCart Accessibility Mode, Samira Khan. Our anticipatory female voice assistant is ready. Speak what you want to buy..."*
4. Click **"🎙️ Voice Search"** and speak:
   > *"Show me black pair of jeans Tanaro 32 waist for my brother"*
5. AnticipateCart reads the result aloud in the female voice:
   > *"Tanaro Black Pair of Jeans Size 32, 2,499 Rupees. What it is used for: Premium stretch denim crafted for all-day comfort and sharp everyday styling."*
6. Speak or click: *"Add to cart"*. The female assistant confirms: *"Added Tanaro Black Pair of Jeans to cart. Say place order to checkout."*
7. Speak: *"Place order"*. The assistant enforces voice safety:
   > *"You have 1 item totaling 2,499 Rupees in your cart. Say yes or confirm to place this order now."*
8. Speak: *"Yes confirm"*. The order is placed and the female voice confirms!

---

### ACT 4: Restock Alerts & Admin Inventory Toggle (2:15 - 3:00)
**Presenter**:
> *"When items are out of stock, AnticipateCart turns lost sales into automated conversions. Watch this live restock alert."*

**Action**:
1. In the search bar, search for an out-of-stock item or show the catalogue. The card shows **"Out of Stock"** with a **"🔔 Notify Me"** button.
2. Click **"Notify Me"**. The shopper is registered in SQLite `restock_subscriptions`.
3. Now open the **"⚡ Admin Restock Demo"** modal.
4. Locate the item (Stock: 0). Click **"⚡ Restock (15)"**.
5. The admin endpoint `/api/admin/stock` executes.
6. Instantly, the accessibility assistant speaks aloud:
   > *"Notification: Restock Alert! [Product Title] is now back in stock with 15 units available!"*
7. Show the notification recorded in SQLite and the updated badge on the product card.

**Presenter Closing**:
> *"AnticipateCart delivers 100% precision, zero wrong commits, and saves an average of over 2 words per query, all backed by Rezolve Labs semantic search and universal voice accessibility. Thank you!"*
