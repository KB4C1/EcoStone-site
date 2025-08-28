window.addEventListener("DOMContentLoaded", () => {
  document.querySelector(".decor-line2").classList.add("active");
  document.querySelector(".decor-line3").classList.add("active");
});

async function loadProducts() {
    try {
        const res = await fetch("https://ecostone.onrender.com:443/products");
        if (!res.ok) throw new Error("Помилка завантаження товарів");

        const products = await res.json();
        const container = document.getElementById("catalog-container");
        container.innerHTML = "";

        products.forEach(p => {
            const card = document.createElement("div");
            card.className = "product";
            card.innerHTML = `
                <img src="https://ecostone.onrender.com:443${p.image_path}" alt="${p.name}">
                <h3>${p.name}</h3>
                <p>${p.price_per_kg} грн/кг</p>
                <button class="order-btn">Замовити</button>
            `;
            container.appendChild(card);

            const btn = card.querySelector(".order-btn");
            btn.addEventListener("click", () => addToCart(p));
        });
    } catch (err) {
        console.error(err);
        alert("Не вдалося завантажити товари 😢");
    }
}

function addToCart(product) {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];
    const found = cart.find(item => item.name === product.name);

    if (found) {
        found.count += 1;
    } else {
        cart.push({ name: product.name, price: product.price_per_kg, count: 1 });
    }

    localStorage.setItem("cart", JSON.stringify(cart));
    alert(`${product.name} додано у корзину ✅`);
}

window.addEventListener("DOMContentLoaded", loadProducts);
