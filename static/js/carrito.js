/**
 * Agrega un producto al carrito, actualizando el inventario en la interfaz y manejando errores.
 * @param {number} productoId - El ID del producto que se va a agregar.
 */
function agregarAlCarrito(productoId) {
    const cantidad = document.getElementById(`cantidad-${productoId}`).value;

    fetch('/agregar_carrito', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            producto_id: productoId,
            cantidad: parseInt(cantidad, 10),
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            // Actualizar la cantidad disponible en la interfaz
            document.getElementById(`cantidad-disponible-${productoId}`).textContent -= cantidad;
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ocurrió un error al intentar agregar el producto al carrito. Inténtalo de nuevo.');
    });
}

/**
 * Elimina un producto del carrito y restaura el inventario.
 @param {number} productoId - El ID del producto que se va a eliminar.
 */
 function eliminarDelCarrito(productoId) {
    fetch(`/eliminar_carrito?id_producto=${productoId}`, {
        method: 'GET', // Cambia a POST si usas ese método en el backend
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            location.reload();  // Recargar la página para reflejar los cambios
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ocurrió un error al eliminar el producto del carrito. Inténtalo de nuevo.');
    });
}
function mostrarCategoria(categoria) {
    // Ocultar todas las secciones de productos
    const secciones = document.querySelectorAll('.productos-grid');
    secciones.forEach(section => {
        section.style.display = 'none';
    });

    // Mostrar la sección de la categoría seleccionada
    const seleccionada = document.getElementById(categoria);
    if (seleccionada) {
        seleccionada.style.display = 'grid';
    }
}

// Mostrar la primera categoría al cargar
document.addEventListener('DOMContentLoaded', () => {
    const botones = document.querySelectorAll('.categoria-button');
    if (botones.length > 0) {
        mostrarCategoria(botones[0].innerText.trim().replace(" ", "_").toLowerCase());
    }
});
