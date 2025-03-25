

const GET_OUTSTANDING_URL = "/app/outstanding/get-outstanding";
const ALLOWED_DIFF = 10 ; 

function addEventListeners(static) { 
    document.querySelectorAll('.field-bill select').forEach((input,i) => {
        input.onchange  = (e) => {
            const id = e.target.value;
            if (id) {
                fetchOutstanding(id,i,static);
            }
        };
    });
}

function fetchOutstanding(id,i,static) {
    fetch(`${GET_OUTSTANDING_URL}/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.querySelectorAll('.field-balance')[i].innerText = data.balance ;
            document.querySelectorAll('.field-date')[i+1].innerText = data.date ;
            const amt_input = document.querySelectorAll('.field-amt')[i+1].querySelector("input")
            if (amt_input.value == "") { amt_input.value = parseInt(data.balance) ; }
        })
        .catch(error => console.error('Error fetching outstanding:', error));
}

function validateAmounts() {
    const txt = document.querySelector('.field-amt input').value ; 
        const totalAmount = parseFloat( txt );
        let totalCollectionAmount = 0;
        document.querySelectorAll('.field-amt input').forEach((input,idx) => {
            if (idx == 0) { return ; }
            const delete_checkbox = document.querySelectorAll('input[name$="DELETE"]')[idx]
            if (!(delete_checkbox && delete_checkbox.checked)) { 
                const value = parseFloat(input.value);
                if (!isNaN(value)) {
                    totalCollectionAmount += value;
                }
            }
        });
        const difference = Math.abs(totalAmount - totalCollectionAmount);
        if (difference > ALLOWED_DIFF) {
            alert(`Mismatch between total collection amount (${totalCollectionAmount}) and bill wise amount (${totalAmount}). \n Please correct the values.`);
            return false;
        }
        return true;   
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#id_customer').onchange = (e) => {
        document.querySelectorAll('.field-customer input').forEach((input,i) => {
             input.value = document.querySelector('#id_customer').value ; 
        });
    }

    document.querySelector('#collection_form').addEventListener('submit', function(e) {
        if (!validateAmounts()) {
            e.preventDefault();
        }
    });
    addEventListeners(true); 
});

document.addEventListener('formset:added', function() {
    addEventListeners(false);
})
