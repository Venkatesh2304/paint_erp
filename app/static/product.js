

const GET_PRODUCT_URL = "/app/product/get-info";
const ALLOWED_DIFF = 10 ; 

function addEventListeners(static) { 

    document.querySelectorAll('.field-product select').forEach((input,i) => {
        input.onchange  = (e) => {
            const id = e.target.value;
            if (id) {
                fetchProduct(id,i,static);
            }
        };
    });

    if (document.querySelector('.field-dpl input')) {
    
        document.querySelectorAll('.field-margin input').forEach((input,i) => {
        input.onchange = (e) => {
            const margin = e.target.value;
            const cost = document.querySelectorAll('.field-dpl input')[i].value;
            const price = parseFloat(cost) + (parseFloat(cost) * parseFloat(margin) / 100);
            document.querySelectorAll('.field-price input')[i].value = price.toFixed(2);
        }
        });

        document.querySelectorAll('.field-price input').forEach((input,i) => {
            input.onchange = (e) => {
                const price = e.target.value;
                const cost = document.querySelectorAll('.field-dpl input')[i].value;
                const margin = ((parseFloat(price) - parseFloat(cost)) / parseFloat(cost)) * 100;
                document.querySelectorAll('.field-margin input')[i].value = margin.toFixed(2);
            }
        });

    }

}

function fetchProduct(id,i,static) {
    fetch(`${GET_PRODUCT_URL}/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.querySelectorAll('.field-dpl input')[i].value = data.dpl ;
            document.querySelectorAll('.field-price input')[i].value = data.dpl ;
        })
        .catch(error => console.error('Error fetching product:', error));
}


document.addEventListener('DOMContentLoaded', function() {
    addEventListeners(true); 
});

document.addEventListener('formset:added', function() {
    addEventListeners(false);
})
