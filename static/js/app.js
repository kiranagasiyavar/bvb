// static/js/app.js - AnticipateCart Frontend Engine with Female Voice & Visual Intelligence

class AnticipateCartApp {
  constructor() {
    this.currentUser = {
      id: "usr_std_01",
      name: "Alex Johnson",
      type: "standard",
      speechRate: 1.0,
      fontSize: "normal"
    };
    
    this.ws = null;
    this.recognition = null;
    this.synth = window.speechSynthesis;
    this.femaleVoices = [];
    this.selectedVoice = null;
    this.isListening = false;
    this.streamingWords = [];
    this.typingTimer = null;
    this.pendingConfirmOrder = false;
    this.simulatedStreamInterval = null;
    this.startTime = Date.now();
    
    this.init();
  }

  async init() {
    this.initWebSocket();
    this.initVoices();
    this.initSpeechRecognition();
    this.bindEvents();
    await this.fetchProducts();
    await this.checkNotifications();
    
    const savedUser = localStorage.getItem("anticipate_user");
    if (savedUser) {
      try {
        this.setUser(JSON.parse(savedUser));
      } catch (e) {}
    } else {
      this.setUser(this.currentUser);
    }
  }

  // ----------------- Female Voice Initialization -----------------
  initVoices() {
    const loadVoices = () => {
      const allVoices = this.synth ? this.synth.getVoices() : [];
      if (!allVoices || allVoices.length === 0) return;

      // Identify female voices based on name keywords & language
      const femaleKeywords = [
        "female", "zira", "samantha", "victoria", "karen", "moira", "tessa",
        "heera", "neerja", "swara", "priya", "google uk english female",
        "google us english", "microsoft zira", "microsoft heera", "microsoft swara",
        "serena", "agnes", "fiona", "monica", "paulina"
      ];

      this.femaleVoices = allVoices.filter(v => {
        const nameLower = v.name.toLowerCase();
        return femaleKeywords.some(kw => nameLower.includes(kw));
      });

      // If no explicit female match found, use standard English voices with high pitch
      if (this.femaleVoices.length === 0) {
        this.femaleVoices = allVoices.filter(v => v.lang.startsWith("en"));
      }
      if (this.femaleVoices.length === 0) {
        this.femaleVoices = allVoices;
      }

      // Default to best natural female voice
      this.selectedVoice = this.femaleVoices.find(v => 
        v.name.toLowerCase().includes("zira") || 
        v.name.toLowerCase().includes("samantha") ||
        v.name.toLowerCase().includes("female") ||
        v.name.toLowerCase().includes("google uk english female")
      ) || this.femaleVoices[0];

      this.populateVoiceSelect();
      this.updateVoiceBadge();
    };

    loadVoices();
    if (this.synth && this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = loadVoices;
    }
  }

  populateVoiceSelect() {
    const sel = document.getElementById("voiceSelect");
    if (!sel) return;
    sel.innerHTML = "";
    
    this.femaleVoices.forEach((v, idx) => {
      const opt = document.createElement("option");
      opt.value = idx;
      opt.textContent = `👩 ${v.name} (${v.lang})`;
      if (this.selectedVoice && v.name === this.selectedVoice.name) {
        opt.selected = true;
      }
      sel.appendChild(opt);
    });

    sel.onchange = (e) => {
      const chosen = this.femaleVoices[parseInt(e.target.value)];
      if (chosen) {
        this.selectedVoice = chosen;
        this.updateVoiceBadge();
        this.speak("Female voice active. AnticipateCart voice navigation ready.");
      }
    };
  }

  updateVoiceBadge() {
    const badge = document.getElementById("femaleVoiceBadge");
    if (badge && this.selectedVoice) {
      badge.innerHTML = `<span class="pulse-dot"></span> 👩 Voice: <strong>${this.selectedVoice.name.split(" ")[0]} (Female)</strong>`;
    }
  }

  speak(text) {
    if (!this.synth) return;
    this.synth.cancel(); // Stop pending speech
    
    const utterance = new SpeechSynthesisUtterance(text);
    if (this.selectedVoice) {
      utterance.voice = this.selectedVoice;
    }
    // Set natural, bright female pitch
    utterance.pitch = 1.15;
    utterance.rate = this.currentUser.speechRate || 1.0;
    
    this.showVoiceSpeakingPill(true, text);
    this.setEqualizer(true);
    
    utterance.onend = () => {
      this.showVoiceSpeakingPill(false);
      this.setEqualizer(false);
    };
    utterance.onerror = () => {
      this.showVoiceSpeakingPill(false);
      this.setEqualizer(false);
    };
    
    this.synth.speak(utterance);
  }

  setEqualizer(active) {
    const eqs = document.querySelectorAll(".audio-equalizer");
    eqs.forEach(eq => {
      if (active) eq.classList.add("active");
      else eq.classList.remove("active");
    });
  }

  showVoiceSpeakingPill(show, text = "") {
    const pill = document.getElementById("voiceSpeakingIndicator");
    const txt = document.getElementById("voiceSpeakingText");
    if (pill) {
      if (show) {
        pill.classList.add("active");
        if (txt) txt.textContent = text.length > 55 ? text.substring(0, 52) + "..." : text;
      } else {
        pill.classList.remove("active");
      }
    }
  }

  // ----------------- WebSocket Management -----------------
  initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/anticipate`;
    
    try {
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log("[AnticipateCart] Connected to anticipatory stream socket.");
        this.updateSocketStatus(true);
      };
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "anticipation_update") {
          this.handleAnticipationUpdate(data);
        }
      };
      
      this.ws.onclose = () => {
        this.updateSocketStatus(false);
        setTimeout(() => this.initWebSocket(), 2000);
      };
      
      this.ws.onerror = (err) => {
        console.error("[AnticipateCart] Stream socket error:", err);
      };
    } catch (e) {
      console.error("Failed to connect WebSocket:", e);
    }
  }

  updateSocketStatus(connected) {
    const pill = document.getElementById("adapterPill");
    if (pill) {
      pill.textContent = connected ? "⚡ Quantum Stream Active" : "Connecting...";
      pill.style.borderColor = connected ? "var(--accent-cyan)" : "var(--accent-rose)";
    }
  }

  sendTokensToStream(words, isFinal = false) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "token_stream",
        words: words,
        is_final: isFinal
      }));
    }
  }

  resetStream() {
    this.streamingWords = [];
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "reset" }));
    }
    this.clearPredictionUI();
  }

  // ----------------- Anticipation Handler -----------------
  handleAnticipationUpdate(data) {
    // 1. Render Token Chips
    const tokenBox = document.getElementById("tokenStreamBox");
    tokenBox.innerHTML = "";
    data.words.forEach((w, idx) => {
      const chip = document.createElement("span");
      chip.className = "token-chip";
      chip.innerHTML = `<span style="color:var(--accent-cyan); font-size:0.75rem;">#${idx+1}</span> ${w}`;
      tokenBox.appendChild(chip);
    });

    // 2. Render Filters & Confidences
    const filters = data.filters;
    const confs = data.confidences;
    
    this.updateFilterCard("Category", filters.category, confs.category);
    this.updateFilterCard("Brand", filters.brand, confs.brand);
    this.updateFilterCard("Colour", filters.colour, confs.colour);
    this.updateFilterCard("Size", filters.size, confs.size);
    this.updateFilterCard("Budget", filters.budget ? `₹${Number(filters.budget).toLocaleString()}` : null, confs.budget);

    // 3. Overall Confidence
    const overallPct = Math.round(data.overall_confidence * 100);
    document.getElementById("overallConfVal").textContent = `${overallPct}%`;
    document.getElementById("overallConfBar").style.width = `${overallPct}%`;

    // 4. Update Radar Stats HUD
    const hudTokens = document.getElementById("radarTokenCount");
    const hudConf = document.getElementById("radarConfidence");
    const hudSaved = document.getElementById("radarWordsSaved");
    if (hudTokens) hudTokens.textContent = data.word_count || 0;
    if (hudConf) hudConf.textContent = `${overallPct}%`;

    // 5. Commit Status
    const banner = document.getElementById("commitBanner");
    const statusText = document.getElementById("commitStatusText");
    const reasonText = document.getElementById("commitReasonText");

    if (data.decision === "COMMIT") {
      banner.className = "commit-banner committed";
      const wordsSaved = Math.max(0, 2);
      if (hudSaved) hudSaved.textContent = `+${wordsSaved} words`;
      statusText.innerHTML = `🎯 <strong>COMMITTED!</strong> Top Candidate Decisive (Saved ~${wordsSaved} words)`;
      reasonText.textContent = `${data.reason} (Score Gap: ${data.score_gap || 0.4})`;
      
      // Accessibility Spoken announcement via Female Voice
      if (this.currentUser.type === "accessibility" && data.spoken_line) {
        this.speak(data.spoken_line);
      }
    } else {
      banner.className = "commit-banner waiting";
      if (hudSaved) hudSaved.textContent = "0 words";
      statusText.innerHTML = `⏳ <strong>SCANNING & WAITING...</strong> Confidence: ${overallPct}% (Threshold: 85%)`;
      reasonText.textContent = data.reason;
    }

    // 6. Mid-Stream Corrections Alert
    const corrBox = document.getElementById("correctionsBox");
    if (data.events && data.events.length > 0) {
      corrBox.style.display = "flex";
      corrBox.innerHTML = `⚠️ <strong>Mid-Stream Retraction:</strong> ${data.events.join(" | ")}`;
    } else {
      corrBox.style.display = "none";
    }

    // 7. Render matching search results with photos
    if (data.search_results && data.search_results.length > 0) {
      this.renderProducts(data.search_results.map(r => r.product), data.committed_product?.id);
    }
  }

  updateFilterCard(name, value, conf) {
    const valEl = document.getElementById(`val${name}`);
    const barEl = document.getElementById(`bar${name}`);
    if (valEl && barEl) {
      valEl.textContent = value || "—";
      const pct = Math.round((conf || 0) * 100);
      barEl.style.width = `${pct}%`;
      barEl.style.background = conf >= 0.85 ? "var(--accent-green)" : "var(--accent-cyan)";
    }
  }

  clearPredictionUI() {
    ["Category", "Brand", "Colour", "Size", "Budget"].forEach(k => {
      this.updateFilterCard(k, null, 0);
    });
    document.getElementById("overallConfVal").textContent = "0%";
    document.getElementById("overallConfBar").style.width = "0%";
    const banner = document.getElementById("commitBanner");
    banner.className = "commit-banner waiting";
    document.getElementById("commitStatusText").innerHTML = "Ready to anticipate...";
    document.getElementById("commitReasonText").textContent = "Type or speak to start anticipatory session.";
    document.getElementById("tokenStreamBox").innerHTML = '<span style="color:var(--text-muted);">Word tokens will stream here...</span>';
    document.getElementById("correctionsBox").style.display = "none";
  }

  // ----------------- Web Speech API (SpeechRecognition) -----------------
  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("Web Speech API not supported.");
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = "en-IN"; // English (India) with Hindi code-mix

    this.recognition.onstart = () => {
      this.isListening = true;
      const btn = document.getElementById("btnVoiceInput");
      btn.classList.add("listening");
      btn.innerHTML = `🎙️ Listening...`;
      this.showVoiceSpeakingPill(true, "Listening to your voice...");
    };

    this.recognition.onresult = (event) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      const activeText = (final || interim).trim();
      if (!activeText) return;

      document.getElementById("searchInput").value = activeText;
      const tokens = activeText.split(/\s+/).filter(Boolean);

      if (this.currentUser.type === "accessibility" && final) {
        this.handleVoiceCommand(final);
      } else {
        this.sendTokensToStream(tokens, Boolean(final));
      }
    };

    this.recognition.onerror = (e) => {
      this.stopListening();
    };

    this.recognition.onend = () => {
      if (this.isListening) {
        try { this.recognition.start(); } catch (e) {}
      } else {
        this.stopListening();
      }
    };
  }

  toggleVoiceInput() {
    if (!this.recognition) {
      alert("Web Speech Recognition is not supported on this browser.");
      return;
    }
    if (this.isListening) {
      this.stopListening();
    } else {
      this.resetStream();
      try {
        this.recognition.start();
      } catch (e) {
        this.stopListening();
      }
    }
  }

  stopListening() {
    this.isListening = false;
    if (this.recognition) {
      try { this.recognition.stop(); } catch (e) {}
    }
    const btn = document.getElementById("btnVoiceInput");
    if (btn) {
      btn.classList.remove("listening");
      btn.innerHTML = `🎙️ Voice Search`;
    }
    this.showVoiceSpeakingPill(false);
  }

  // ----------------- Accessibility Voice Command Dispatcher -----------------
  async handleVoiceCommand(transcript) {
    const res = await fetch("/api/voice/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: this.currentUser.id, transcript: transcript })
    });
    const data = await res.json();
    
    if (data.spoken_response) {
      this.speak(data.spoken_response);
    }
    
    if (data.action_data?.action === "order_confirmed") {
      this.openOrderSuccessModal(data.action_data.order);
      await this.fetchCart();
    } else if (data.action_data?.action === "view_cart") {
      this.openCartModal();
    } else if (data.action_data?.action === "search_results") {
      const prods = data.action_data.search_res.results.map(r => r.product);
      this.renderProducts(prods);
    }
  }

  // ----------------- User Persona Management -----------------
  setUser(user) {
    this.currentUser = user;
    localStorage.setItem("anticipate_user", JSON.stringify(user));
    
    const pill = document.getElementById("currentUserPill");
    if (pill) {
      pill.textContent = user.type === "accessibility" ? "♿ Lumina Voice Mode" : "✨ Cyber Standard Mode";
    }

    const accBar = document.getElementById("accessibilityBar");
    if (user.type === "accessibility") {
      document.body.classList.add("accessibility-mode");
      if (accBar) accBar.style.display = "flex";
      this.speak(
        `Welcome to AnticipateCart Accessibility Voice Mode, ${user.name}. ` +
        `Our female voice assistant is online. Speak what you wish to buy.`
      );
    } else {
      document.body.classList.remove("accessibility-mode");
      if (accBar) accBar.style.display = "none";
    }
  }

  toggleUserRole() {
    if (this.currentUser.type === "standard") {
      this.setUser({
        id: "usr_acc_01",
        name: "Samira Khan",
        type: "accessibility",
        speechRate: 1.0,
        fontSize: "large"
      });
    } else {
      this.setUser({
        id: "usr_std_01",
        name: "Alex Johnson",
        type: "standard",
        speechRate: 1.0,
        fontSize: "normal"
      });
    }
  }

  // ----------------- Products & Real Images Rendering -----------------
  async fetchProducts() {
    try {
      const res = await fetch("/api/products?limit=30");
      const data = await res.json();
      this.renderProducts(data.products || []);
    } catch (e) {
      console.error("Failed to fetch products:", e);
    }
  }

  getColorHex(colorName) {
    const map = {
      black: "#000000", white: "#ffffff", red: "#ef4444", blue: "#3b82f6",
      navy: "#1e3a8a", green: "#10b981", grey: "#64748b", yellow: "#f59e0b",
      brown: "#78350f", beige: "#f5f5dc", olive: "#65a30d", pink: "#ec4899"
    };
    return map[colorName.toLowerCase()] || "#94a3b8";
  }

  renderProducts(products, committedId = null) {
    const grid = document.getElementById("productsGrid");
    grid.innerHTML = "";
    
    if (!products || products.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
        <div style="font-size:3rem; margin-bottom:0.5rem;">🔍</div>
        <h3>No matching products found</h3>
        <p>Try searching for brand, category, colour or size</p>
      </div>`;
      return;
    }

    products.forEach((p) => {
      const isCommitted = p.id === committedId;
      const isOOS = p.stock === 0;
      const colorHex = this.getColorHex(p.colour || "black");
      const imgUrl = p.image_url || "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80";

      const card = document.createElement("div");
      card.className = `product-card ${isCommitted ? "early-match" : ""}`;
      card.setAttribute("tabindex", "0");
      card.setAttribute("aria-label", `${p.title}, ${p.price} Rupees, ${p.usage || ""}`);

      card.innerHTML = `
        <div class="product-image-box">
          <img src="${imgUrl}" alt="${p.title}" class="product-image" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80'">
          <div class="product-image-overlay">
            <span class="color-swatch-pill">
              <span class="color-swatch-circle" style="background:${colorHex};"></span>
              ${p.colour.toUpperCase()}
            </span>
            ${isCommitted ? `<span class="badge-brand" style="background:var(--accent-green); color:#000; font-weight:800; padding:0.25rem 0.6rem; border-radius:12px; font-size:0.75rem;">🎯 EARLY COMMIT MATCH</span>` : ""}
          </div>
        </div>

        <div class="product-card-body">
          <div>
            ${p.usage ? `<div class="usage-badge">💡 What it's used for: ${p.usage}</div>` : ""}
            <h3 class="product-title">${p.title}</h3>
            <div class="product-meta">
              <span class="meta-pill">🏷️ ${p.brand}</span>
              <span class="meta-pill">📂 ${p.category}</span>
              <span class="meta-pill">📏 Size: ${p.size}</span>
            </div>
          </div>

          <div>
            <div class="product-price-stock">
              <span class="product-price">₹${Number(p.price).toLocaleString()}</span>
              <span class="stock-pill ${isOOS ? "out-of-stock" : "in-stock"}">
                ${isOOS ? "⛔ Out of Stock" : `● ${p.stock} in stock`}
              </span>
            </div>
            
            <div style="display:flex; gap:0.5rem; margin-top:0.6rem;">
              ${!isOOS ? `
                <button class="btn btn-primary" style="flex:1;" onclick="app.addToCart('${p.id}')">
                  🛒 Add to Cart
                </button>
              ` : `
                <button class="btn btn-accent" style="flex:1;" onclick="app.subscribeRestock('${p.id}')">
                  🔔 Notify Me
                </button>
              `}
              <button class="btn" style="padding:0.6rem; min-height:48px;" title="Listen to product description with female voice" onclick="app.speakProduct('${p.id}')">
                🔊
              </button>
            </div>
          </div>
        </div>
      `;
      grid.appendChild(card);
    });
  }

  async speakProduct(productId) {
    const res = await fetch(`/api/products/${productId}`);
    const data = await res.json();
    const p = data.product;
    const text = `${p.title} by ${p.brand}, ${Number(p.price).toLocaleString()} Rupees. What it is used for: ${p.usage}`;
    this.speak(text);
  }

  // ----------------- Cart & Checkout -----------------
  async addToCart(productId) {
    const res = await fetch("/api/cart/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: this.currentUser.id, product_id: productId, quantity: 1 })
    });
    const data = await res.json();
    if (data.success) {
      if (this.currentUser.type === "accessibility") {
        this.speak(`${data.message}. Say view cart or place order to checkout.`);
      }
      this.updateCartBadge();
    }
  }

  async fetchCart() {
    const res = await fetch(`/api/cart?user_id=${this.currentUser.id}`);
    const data = await res.json();
    return data;
  }

  async updateCartBadge() {
    const cart = await this.fetchCart();
    const badge = document.getElementById("cartCountBadge");
    if (badge) badge.textContent = cart.count || 0;
  }

  async openCartModal() {
    const cart = await this.fetchCart();
    const modal = document.getElementById("cartModal");
    const container = document.getElementById("cartItemsContainer");
    const totalEl = document.getElementById("cartTotalAmount");
    
    container.innerHTML = "";
    if (cart.items.length === 0) {
      container.innerHTML = "<p style='color:var(--text-muted); text-align:center; padding:1.5rem;'>Your cart is currently empty.</p>";
      totalEl.textContent = "₹0";
    } else {
      cart.items.forEach(it => {
        const row = document.createElement("div");
        row.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding:0.75rem 0; border-bottom:1px solid var(--border-color);";
        row.innerHTML = `
          <div style="display:flex; align-items:center; gap:0.75rem;">
            <img src="${it.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=200&q=80'}" style="width:50px; height:50px; object-fit:cover; border-radius:8px;">
            <div>
              <strong>${it.title}</strong>
              <div style="font-size:0.85rem; color:var(--text-muted);">Qty: ${it.quantity} × ₹${Number(it.price).toLocaleString()}</div>
            </div>
          </div>
          <span style="font-weight:800; color:var(--accent-green); font-size:1.1rem;">₹${(it.price * it.quantity).toLocaleString()}</span>
        `;
        container.appendChild(row);
      });
      totalEl.textContent = `₹${Number(cart.total_amount).toLocaleString()}`;
    }
    
    modal.classList.add("open");
  }

  closeCartModal() {
    document.getElementById("cartModal").classList.remove("open");
  }

  async placeOrder() {
    if (this.currentUser.type === "accessibility" && !this.pendingConfirmOrder) {
      this.pendingConfirmOrder = true;
      this.speak("You are placing an order. Please say yes or confirm to finalize your purchase.");
      return;
    }

    try {
      const res = await fetch("/api/orders/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: this.currentUser.id })
      });
      const data = await res.json();
      if (data.success) {
        this.pendingConfirmOrder = false;
        this.closeCartModal();
        this.openOrderSuccessModal(data);
        this.updateCartBadge();
        if (this.currentUser.type === "accessibility") {
          this.speak(`Order ${data.order_id} placed successfully! Thank you for shopping with AnticipateCart.`);
        }
      }
    } catch (e) {
      console.error("Order error:", e);
    }
  }

  openOrderSuccessModal(order) {
    const modal = document.getElementById("orderSuccessModal");
    document.getElementById("orderIdSpan").textContent = order.order_id;
    document.getElementById("orderAmountSpan").textContent = `₹${Number(order.total_amount).toLocaleString()}`;
    modal.classList.add("open");
  }

  closeOrderSuccessModal() {
    document.getElementById("orderSuccessModal").classList.remove("open");
  }

  // ----------------- Restock Subscription & Notifications -----------------
  async subscribeRestock(productId) {
    const res = await fetch("/api/restock/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: this.currentUser.id, product_id: productId })
    });
    const data = await res.json();
    alert("Subscribed! We will notify you immediately once stock arrives.");
    if (this.currentUser.type === "accessibility") {
      this.speak("You are subscribed to restock notifications for this item.");
    }
  }

  async checkNotifications() {
    try {
      const res = await fetch(`/api/notifications?user_id=${this.currentUser.id}`);
      const data = await res.json();
      const notifs = data.notifications || [];
      
      if (this.currentUser.type === "accessibility") {
        for (const n of notifs) {
          if (!n.is_spoken) {
            this.speak(`Notification: ${n.title}. ${n.message}`);
            await fetch(`/api/notifications/${n.id}/spoken`, { method: "POST" });
          }
        }
      }
    } catch (e) {}
  }

  // ----------------- Image Search -----------------
  async handleImageUpload(file) {
    const formData = new FormData();
    formData.append("file", file);
    
    document.getElementById("tokenStreamBox").innerHTML = '<span style="color:var(--accent-cyan);">🔍 Visual Cognition: Extracting product embeddings with Vision Model...</span>';
    
    try {
      const res = await fetch("/api/image-search", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      
      const attrs = data.detected_attributes;
      const chipText = `📷 Vision Detected: ${attrs.colour || ""} ${attrs.category || ""}`;
      document.getElementById("tokenStreamBox").innerHTML = `<span class="token-chip" style="background:#0284c7;">${chipText}</span>`;
      
      const prods = data.results.map(r => r.product);
      this.renderProducts(prods);
      
      if (this.currentUser.type === "accessibility") {
        this.speak(`Image analysis detected ${attrs.colour} ${attrs.category}. Found ${prods.length} matching products.`);
      }
    } catch (e) {
      console.error("Image search failed:", e);
    }
  }

  // ----------------- Admin Demo Drawer -----------------
  async openAdminModal() {
    const res = await fetch("/api/admin/catalogue-summary");
    const data = await res.json();
    
    const container = document.getElementById("adminOosContainer");
    container.innerHTML = "";
    
    data.out_of_stock_samples.forEach(item => {
      const row = document.createElement("div");
      row.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding:0.75rem 0; border-bottom:1px solid var(--border-color);";
      row.innerHTML = `
        <div>
          <strong>${item.title}</strong>
          <div style="font-size:0.85rem; color:var(--text-muted);">${item.brand} | ₹${item.price} | Stock: 0</div>
        </div>
        <button class="btn btn-accent" style="padding:0.4rem 0.8rem; font-size:0.85rem;" onclick="app.adminRestockItem('${item.id}', 15)">
          ⚡ Restock (15)
        </button>
      `;
      container.appendChild(row);
    });
    
    document.getElementById("adminModal").classList.add("open");
  }

  async adminRestockItem(productId, newStock) {
    const res = await fetch("/api/admin/stock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, new_stock: newStock })
    });
    const data = await res.json();
    alert(`Restocked! Dispatched ${data.details.notified_user_count} live notifications.`);
    this.closeAdminModal();
    await this.fetchProducts();
    await this.checkNotifications();
  }

  closeAdminModal() {
    document.getElementById("adminModal").classList.remove("open");
  }

  // ----------------- Simulated Word-by-Word Demo -----------------
  playSimulatedQuery(queryText) {
    if (this.simulatedStreamInterval) {
      clearInterval(this.simulatedStreamInterval);
    }
    this.resetStream();
    const words = queryText.split(" ");
    let idx = 0;
    const input = document.getElementById("searchInput");
    input.value = "";

    this.simulatedStreamInterval = setInterval(() => {
      if (idx < words.length) {
        input.value = words.slice(0, idx + 1).join(" ");
        const tokensSoFar = words.slice(0, idx + 1);
        const isLast = (idx === words.length - 1);
        this.sendTokensToStream(tokensSoFar, isLast);
        idx++;
      } else {
        clearInterval(this.simulatedStreamInterval);
      }
    }, 420);
  }

  // ----------------- UI Event Bindings -----------------
  bindEvents() {
    const searchInput = document.getElementById("searchInput");
    
    searchInput.addEventListener("input", (e) => {
      clearTimeout(this.typingTimer);
      const text = e.target.value.trim();
      if (!text) {
        this.resetStream();
        this.fetchProducts();
        return;
      }

      this.typingTimer = setTimeout(() => {
        const tokens = text.split(/\s+/).filter(Boolean);
        this.sendTokensToStream(tokens, false);
      }, 70);
    });

    searchInput.addEventListener("keydown", async (e) => {
      if (e.key === "Enter") {
        const text = e.target.value.trim();
        if (!text) return;
        
        const res = await fetch("/api/spellcheck", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: text })
        });
        const spellData = await res.json();
        
        if (spellData.was_changed) {
          const banner = document.getElementById("spellcheckBanner");
          banner.style.display = "flex";
          banner.innerHTML = `
            <span>Showing results for <strong>${spellData.corrected}</strong> (corrected from <em>${spellData.original}</em>)</span>
            <button class="btn" style="padding:0.2rem 0.6rem; font-size:0.8rem;" onclick="app.undoSpellcheck('${spellData.original}')">Undo</button>
          `;
          searchInput.value = spellData.corrected;
          this.sendTokensToStream(spellData.corrected.split(/\s+/), true);
        } else {
          document.getElementById("spellcheckBanner").style.display = "none";
          this.sendTokensToStream(text.split(/\s+/), true);
        }
      }
    });

    document.getElementById("btnVoiceInput").addEventListener("click", () => {
      this.toggleVoiceInput();
    });

    const imgInput = document.getElementById("imageFileInput");
    imgInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        this.handleImageUpload(e.target.files[0]);
      }
    });

    document.getElementById("btnFontNormal")?.addEventListener("click", () => {
      document.body.classList.remove("font-large", "font-xlarge");
    });
    document.getElementById("btnFontLarge")?.addEventListener("click", () => {
      document.body.classList.remove("font-xlarge");
      document.body.classList.add("font-large");
    });
    document.getElementById("btnFontXLarge")?.addEventListener("click", () => {
      document.body.classList.remove("font-large");
      document.body.classList.add("font-xlarge");
    });

    document.getElementById("speechRateSelect")?.addEventListener("change", (e) => {
      this.currentUser.speechRate = parseFloat(e.target.value);
    });
  }

  undoSpellcheck(orig) {
    document.getElementById("searchInput").value = orig;
    document.getElementById("spellcheckBanner").style.display = "none";
    this.sendTokensToStream(orig.split(/\s+/), true);
  }
}

// Global App Instance
window.app = new AnticipateCartApp();
