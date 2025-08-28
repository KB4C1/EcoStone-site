window.addEventListener("DOMContentLoaded", () => {
    const cartContainer = document.querySelector(".cart-items");
    const cartTotal = document.querySelector(".cart-total");
    let cart = JSON.parse(localStorage.getItem("cart")) || [];

    function saveCart() {
        localStorage.setItem("cart", JSON.stringify(cart));
    }

    function renderCart() {
        cartContainer.innerHTML = "";
        let total = 0;

        if (cart.length === 0) {
            cartContainer.innerHTML = "<p>Ваша корзина порожня 😐</p>";
            cartTotal.innerHTML = `
                <button class="order-btn" disabled>Оформити замовлення</button>
            `;
            return;
        }

        cart.forEach((item, index) => {
            total += item.price * item.count;

            const div = document.createElement("div");
            div.className = "cart-item";
            div.innerHTML = `
                <div class="cart-info">
                    <h3>${item.name}</h3>
                    <p>${item.price} грн/кг</p>
                    <div class="cart-controls">
                        <button class="decrease" data-index="${index}" ${item.count === 1 ? "disabled" : ""}>➖</button>
                        <input type="number" min="1" value="${item.count}" class="count-input" data-index="${index}">
                        <p>кг</p>
                        <button class="increase" data-index="${index}">➕</button>
                    </div>
                </div>
                <button class="remove-item" data-index="${index}">❌</button>
            `;
            cartContainer.appendChild(div);
        });

        cartTotal.innerHTML = `
            <h3>Разом: ${total} грн</h3>
            <button class="order-btn">Оформити замовлення</button>
        `;

        // якщо корзина пуста — кнопка неактивна
        const orderBtn = document.querySelector(".order-btn");
        if (cart.length === 0) {
            orderBtn.disabled = true;
        }

        // ➖
        document.querySelectorAll(".decrease").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const idx = e.target.dataset.index;
                if (cart[idx].count > 1) {
                    cart[idx].count--;
                    saveCart();
                    renderCart();
                }
            });
        });

        // ➕
        document.querySelectorAll(".increase").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const idx = e.target.dataset.index;
                cart[idx].count++;
                saveCart();
                renderCart();
            });
        });

        // 🖊 ручне введення
        document.querySelectorAll(".count-input").forEach(input => {
            input.addEventListener("change", (e) => {
                const idx = e.target.dataset.index;
                let val = parseInt(e.target.value);
                if (isNaN(val) || val < 1) val = 1;
                cart[idx].count = val;
                saveCart();
                renderCart();
            });
        });

        // ❌ видалити товар
        document.querySelectorAll(".remove-item").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const idx = e.target.dataset.index;
                cart.splice(idx, 1);
                saveCart();
                renderCart();
            });
        });

        // 🛒 клік по кнопці замовлення → модалка
        if (orderBtn) {
            orderBtn.addEventListener("click", () => {
                document.querySelector(".modal").classList.add("active");
            });
        }
    }

    renderCart();

    // закриття модалки
    document.querySelector(".modal-close").addEventListener("click", () => {
        document.querySelector(".modal").classList.remove("active");
    });
});
