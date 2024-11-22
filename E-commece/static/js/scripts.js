// scripts.js

// Function to handle adding items to the cart
function addToCart(productId) {
    // Logic to add a product to the cart
    alert(`Produto ${productId} adicionado ao carrinho!`);
}

// Function to remove an item from the cart
function removeFromCart(productId) {
    // Logic to remove a product from the cart
    alert(`Produto ${productId} removido do carrinho!`);
}

// Event listeners for cart buttons (example)
// Assuming there are buttons with class 'btn-add-to-cart' and 'btn-remove-from-cart'
document.addEventListener("DOMContentLoaded", function() {
    const addToCartButtons = document.querySelectorAll('.btn-add-to-cart');
    const removeFromCartButtons = document.querySelectorAll('.btn-remove-from-cart');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            addToCart(productId);
        });
    });

    removeFromCartButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            removeFromCart(productId);
        });
    });
});
