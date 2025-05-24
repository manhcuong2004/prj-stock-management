let initialRows = document.querySelectorAll('.product-row').length;
let formIndex = initialRows;

document.querySelector('#id_stockindetail_set-TOTAL_FORMS').value = initialRows;

const productData = [
    {% for product in products %}
        {
            id: {{ product.id }},
            name: "{{ product.product_name|escapejs }}",
            category_id: {{ product.category.id }},
            purchase_price:{{ product.purchase_price|floatformat:2 }},
        },
    {% endfor %}
];

// Lấy các phần tử select và nút
const categorySelect = document.getElementById('category-select');
const productSelect = document.getElementById('product-select');
const productBatchInput = document.getElementById('product-batch');
const addButton = document.getElementById('add-product-btn');

function resetProductInputs() {
    productSelect.innerHTML = '<option value="">Chọn sản phẩm</option>';
    productSelect.disabled = true;
    productBatchInput.value = '';
    addButton.disabled = true;
}

categorySelect.addEventListener('change', function() {
    const categoryId = this.value;
    resetProductInputs();

    if (categoryId) {
        const filteredProducts = productData.filter(product => product.category_id == categoryId);
        if (filteredProducts.length > 0) {
            filteredProducts.forEach(product => {
                const option = document.createElement('option');
                option.value = product.id;
                option.text = product.name;
                option.dataset.price = product.purchase_price;
                productSelect.appendChild(option);
            });
            productSelect.disabled = false;
        } else {
            productSelect.disabled = true;
        }
    }
});

function updateAddButtonState() {
    addButton.disabled = !(productSelect.value && productBatchInput.value.trim());
}

productSelect.addEventListener('change', updateAddButtonState);
productBatchInput.addEventListener('input', updateAddButtonState);

document.getElementById('add-product-btn').addEventListener('click', function(event) {
    event.preventDefault();
    const productId = productSelect.value;
    const productName = productSelect.options[productSelect.selectedIndex].text;
    const productPrice = parseFloat(productSelect.options[productSelect.selectedIndex].dataset.price) || 0;
    const productBatch = productBatchInput.value.trim();

    if (!productBatch) {
        alert('Vui lòng nhập mã lô!');
        return;
    }

    const existingRows = document.querySelectorAll('.product-row');
    for (let row of existingRows) {
        const rowProductId = row.querySelector('input[name$="-product"]').value;
        const rowProductBatch = row.querySelector('input[name$="-product_batch"]').value;
        if (rowProductId === productId && rowProductBatch === productBatch) {
            alert('Sản phẩm với mã lô này đã tồn tại!');
            return;
        }
    }

    if (productId) {
        const noProductMessage = document.getElementById('no-product-message');
        if (noProductMessage) {
            noProductMessage.style.display = 'none';
        }

        let table = document.querySelector('#product-table');
        if (!table) {
            const tableHTML = `
                <table class="table" id="product-table">
                    <thead>
                        <tr>
                            <th>Tên sản phẩm</th>
                            <th>Mã lô</th>
                            <th>Số lượng</th>
                            <th>Giá nhập</th>
                            <th>Chiết khấu</th>
                            <th>Thành tiền</th>
                            <th>Xóa</th>
                        </tr>
                    </thead>
                    <tbody id="product-list"></tbody>
                </table>
            `;
            const summaryBox = document.querySelector('.summary-box');
            summaryBox.insertAdjacentHTML('afterbegin', tableHTML);
            table = document.querySelector('#product-table');
        }

        const tableBody = document.getElementById('product-list');
        const newRow = document.createElement('tr');
        newRow.classList.add('product-row');
        newRow.innerHTML = `
            <td>
                ${productName}
                <input type="hidden" name="stockindetail_set-${formIndex}-product" value="${productId}">
            </td>
            <td>
                <input type="text" class="form-control" name="stockindetail_set-${formIndex}-product_batch" value="${productBatch}" required>
            </td>
            <td>
                <input type="number" class="form-control quantity" style="width: 100px;" name="stockindetail_set-${formIndex}-quantity" value="1" min="1" required>
            </td>
            <td>
                <span class="price" data-price="${productPrice}">${productPrice.toLocaleString('vi-VN')} đ</span>
            </td>
            <td>
                <div class="input-group" style="max-width: 120px;">
                    <input type="number" class="form-control discount" name="stockindetail_set-${formIndex}-discount" value="0" min="0" max="100" required>
                    <span class="input-group-text">%</span>
                </div>
            </td>
            <td>
                <span class="total">${productPrice.toLocaleString('vi-VN')} đ</span>
            </td>
            <td class="text-center">
                <a href="#" class="delete-row text-danger">Xóa</a>
            </td>
        `;
        tableBody.appendChild(newRow);

        const totalForms = document.querySelector('#id_stockindetail_set-TOTAL_FORMS');
        totalForms.value = parseInt(totalForms.value) + 1;
        formIndex++;
        categorySelect.value = '';
        resetProductInputs();

        updateRowTotals();
        updateSummary();
    }
});

document.addEventListener('click', function(event) {
    if (event.target.classList.contains('delete-row') && event.target.getAttribute('href') === '#') {
        if (confirm('Bạn có chắc muốn xóa sản phẩm này?')) {
            const row = event.target.closest('tr');
            row.remove();
            const totalForms = document.querySelector('#id_stockindetail_set-TOTAL_FORMS');
            totalForms.value = parseInt(totalForms.value) - 1;
            formIndex--;

            updateSummary();

            const visibleRows = document.querySelectorAll('.product-row:not([style*="display: none"])');
            if (visibleRows.length === 0) {
                const table = document.querySelector('#product-table');
                if (table) {
                    table.remove();
                }
                const noProductMessage = document.createElement('p');
                noProductMessage.id = 'no-product-message';
                noProductMessage.textContent = 'Chưa có sản phẩm';
                const summaryBox = document.querySelector('.summary-box');
                summaryBox.insertBefore(noProductMessage, summaryBox.firstChild);
            }
        }
    }
});

function updateRowTotals() {
    document.querySelectorAll('.product-row:not([style*="display: none"])').forEach(row => {
        const quantityInput = row.querySelector('input[name$="-quantity"]');
        const discountInput = row.querySelector('input[name$="-discount"]');
        const priceElement = row.querySelector('.price');

        if (!quantityInput || !discountInput || !priceElement) {
            console.log('Missing quantity, discount, or price element in row:', row);
            return;
        }

        const quantity = parseFloat(quantityInput.value) || 0;
        const price = parseFloat(priceElement.dataset.price) || 0; // Đảm bảo giá trị mặc định
        const discount = parseFloat(discountInput.value) || 0;
        const total = quantity * price * (1 - discount / 100);
        row.querySelector('.total').textContent = total.toLocaleString('vi-VN') + ' đ';
    });
}

document.addEventListener('input', function(event) {
    if (event.target.matches('input[name$="-quantity"]') || event.target.matches('input[name$="-discount"]')) {
        updateRowTotals();
        updateSummary();
    }
});

document.addEventListener('input', function(event) {
    if (event.target.classList.contains('amount-paid')) {
        updateSummary();
    }
});

function updateSummary() {
    let totalAmount = 0;
    let totalDiscount = 0;

    document.querySelectorAll('.product-row:not([style*="display: none"])').forEach(row => {
        const quantityInput = row.querySelector('input[name$="-quantity"]');
        const priceElement = row.querySelector('.price');
        const discountInput = row.querySelector('input[name$="-discount"]');

        if (!quantityInput || !priceElement || !discountInput) {
            return;
        }

        const quantity = parseFloat(quantityInput.value) || 0;
        const price = parseFloat(priceElement.dataset.price) || 0; // Đảm bảo giá trị mặc định
        const discount = parseFloat(discountInput.value) || 0;
        const total = quantity * price * (1 - discount / 100);

        totalAmount += quantity * price;
        totalDiscount += quantity * price * (discount / 100);
    });

    const finalAmount = totalAmount - totalDiscount;
    const amountPaidInput = document.querySelector('.amount-paid');
    const amountPaid = amountPaidInput ? (parseFloat(amountPaidInput.value) || 0) : 0;
    const remainingDebt = finalAmount - amountPaid;

    const totalAmountElement = document.querySelector('.summary-box .total-amount');
    const totalDiscountElement = document.querySelector('.summary-box .total-discount');
    const finalAmountElement = document.querySelector('.summary-box .final-amount');
    const amountPaidDisplayElement = document.querySelector('.summary-box .amount-paid-display');
    const remainingDebtElement = document.querySelector('.summary-box .remaining-debt');
    const actualReceivedElement = document.querySelector('.summary-box .actual-received');

    if (totalAmountElement) totalAmountElement.textContent = totalAmount.toLocaleString('vi-VN') + ' đ';
    if (totalDiscountElement) totalDiscountElement.textContent = totalDiscount.toLocaleString('vi-VN') + ' đ';
    if (finalAmountElement) finalAmountElement.textContent = finalAmount.toLocaleString('vi-VN') + ' đ';
    if (amountPaidDisplayElement) amountPaidDisplayElement.textContent = amountPaid.toLocaleString('vi-VN') + ' đ';
    if (remainingDebtElement) remainingDebtElement.textContent = remainingDebt.toLocaleString('vi-VN') + ' đ';
    if (actualReceivedElement) actualReceivedElement.textContent = amountPaid.toLocaleString('vi-VN') + ' đ';
}

document.addEventListener('DOMContentLoaded', function() {
    resetProductInputs();
    updateRowTotals();
    updateSummary();

    document.querySelectorAll('.product-row').forEach(row => {
        const batchInput = row.querySelector('input[name$="-product_batch"]');
        if (batchInput && batchInput.value) {
            batchInput.setAttribute('value', batchInput.value);
        } else if (batchInput) {
            console.log('Batch input is empty:', batchInput.name);
        }
    });
});

document.getElementById('order-form').addEventListener('submit', function(event) {
    const totalForms = document.querySelector('#id_stockindetail_set-TOTAL_FORMS');
    const rows = document.querySelectorAll('.product-row');
    totalForms.value = rows.length;
    console.log('Submitting form, TOTAL_FORMS:', totalForms.value);
    console.log('Form data:', new FormData(this));
    if (!confirm('Bạn có chắc muốn lưu đơn nhập kho này?')) {
        event.preventDefault();
    }
});