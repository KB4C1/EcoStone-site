const API_URL = "https://ecostone.onrender.com"; // <-- вставляєш тут один раз

window.addEventListener("DOMContentLoaded", () => {
    document.querySelector(".decor-line2").classList.add("active");
    document.querySelector(".decor-line3").classList.add("active");
    loadProducts();
});

async function loadProducts() {
    try {
        const res = await fetch(`${API_URL}/products`);
        if (!res.ok) throw new Error("Помилка завантаження товарів");

        const products = await res.json();
        const container = document.getElementById("catalog-container");
        container.innerHTML = "";

        products.forEach(p => {
            const card = document.createElement("div");
            card.className = "product";
            card.innerHTML = `
                <img src="${API_URL}${p.image_path}" alt="${p.name}">
                <h3>${p.name}</h3>
                <p>${p.price_per_kg} грн/кг</p>
                <button class="order-btn">Замовити</button>
            `;
            container.appendChild(card);

            const btn = card.querySelector(".order-btn");
            btn.addEventListener("click", (event) => addToCart(p, event));
        });
    } catch (err) {
        console.error(err);
        alert("Не вдалося завантажити товари 😢");
    }
}

function addToCart(product, event) {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];
    const found = cart.find(item => item.name === product.name);

    if (found) {
        found.count += 1;
    } else {
        cart.push({ name: product.name, price: product.price_per_kg, count: 1 });
    }

    localStorage.setItem("cart", JSON.stringify(cart));

    const btn = event.target;
    const oldText = btn.textContent;

    btn.textContent = "✅ Успішно додано";
    btn.disabled = true;

    setTimeout(() => {
        btn.textContent = oldText;
        btn.disabled = false;
    }, 2000);
}
