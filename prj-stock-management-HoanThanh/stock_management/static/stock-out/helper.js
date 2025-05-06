let formIndex = {{ formset.total_form_count }};

const productData = [
    {% for product in products %}
        {
            id: {{ product.id }},
            name: "{{ product.product_name|escapejs }}",
            category_id: {{ product.category.id }},
            selling_price: {{ product.selling_price|floatformat:2 }}
        },
    {% endfor %}
];

const batchData = [
    {% for detail in product_details %}
        {
            product_id: {{ detail.product.id }},
            product_batch: "{{ detail.product_batch|escapejs }}",
            remaining_quantity: {{ detail.remaining_quantity }},
            selling_price: {{ detail.product.selling_price|floatformat:2 }},
            expiry_date: "{{ detail.expiry_date|date:'Y-m-d'|default:'' }}"
        },
    {% endfor %}
];

// Handle category selection
document.getElementById('category-select').addEventListener('change', function() {
    const categoryId = this.value;
    const productSelect = document.getElementById('product-select');
    const batchSelect = document.getElementById('batch-select');
    const addButton = document.getElementById('add-product-btn');

    // Reset product and batch selects
    productSelect.innerHTML = '<option value="">Chọn sản phẩm</option>';
    batchSelect.innerHTML = '<option value="">Chọn lô sản phẩm</option>';
    productSelect.disabled = true;
    batchSelect.disabled = true;
    addButton.disabled = true;

    if (categoryId) {
        // Lọc sản phẩm theo danh mục
        const filteredProducts = productData.filter(product => product.category_id == categoryId);
        filteredProducts.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.text = product.name;
            option.dataset.price = product.selling_price;
            productSelect.appendChild(option);
        });
        productSelect.disabled = filteredProducts.length === 0;
    }
});

// Handle product selection
document.getElementById('product-select').addEventListener('change', function() {
    const productId = this.value;
    const batchSelect = document.getElementById('batch-select');
    const addButton = document.getElementById('add-product-btn');

    batchSelect.innerHTML = '<option value="">Chọn lô sản phẩm</option>';
    batchSelect.disabled = true;
    addButton.disabled = true;

    if (productId) {
        // Lọc lô theo sản phẩm
        const filteredBatches = batchData.filter(batch => batch.product_id == productId);
        filteredBatches.forEach(batch => {
            const option = document.createElement('option');
            option.value = batch.product_batch;
            option.text = `${batch.product_batch} (Còn: ${batch.remaining_quantity}${batch.expiry_date ? ', Hết hạn: ' + batch.expiry_date : ''})`;
            option.dataset.price = batch.selling_price;
            batchSelect.appendChild(option);
        });
        batchSelect.disabled = filteredBatches.length === 0;
    }
});

// Enable add button when batch is selected
document.getElementById('batch-select').addEventListener('change', function() {
    const addButton = document.getElementById('add-product-btn');
    addButton.disabled = !this.value;
});

// Handle add product
document.getElementById('add-product-btn').addEventListener('click', function(event) {
    event.preventDefault();
    const productSelect = document.getElementById('product-select');
    const batchSelect = document.getElementById('batch-select');
    const productId = productSelect.value;
    const productName = productSelect.options[productSelect.selectedIndex].text;
    const productPrice = parseFloat(batchSelect.options[batchSelect.selectedIndex].dataset.price) || 0;
    const productBatch = batchSelect.value;

    if (productId && productBatch) {
        const noProductMessage = document.getElementById('no-product-message');
        if (noProductMessage) {
            noProductMessage.style.display = 'none';
        }

        let table = document.querySelector('.table');
        if (!table) {
            const tableHTML = `
                <table class="table">
                    <thead>
                        <tr>
                            <th>Tên sản phẩm</th>
                            <th>Tên lô</th>
                            <th>Số lượng</th>
                            <th>Giá</th>
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
            table = document.querySelector('.table');
        }

        const tableBody = document.getElementById('product-list');
        const newRow = document.createElement('tr');
        newRow.classList.add('product-row');
        newRow.innerHTML = `
            <td>
                <select name="stockoutdetail_set-${formIndex}-product" class="form-control">
                    <option value="${productId}" selected>${productName}</option>
                </select>
                <input type="hidden" name="stockoutdetail_set-${formIndex}-product_batch" value="${productBatch}">
            </td>
            <td>${productBatch}</td>
            <td><input type="number" class="form-control quantity" style="width: 100px;" name="stockoutdetail_set-${formIndex}-quantity" value="1"></td>
            <td>
                <span class="price" data-price="${productPrice}">${productPrice.toLocaleString('vi-VN')} đ</span>
            </td>
            <td>
                <div class="input-group" style="max-width: 120px;">
                    <input type="number" class="form-control discount" name="stockoutdetail_set-${formIndex}-discount" value="0">
                    <span class="input-group-text">%</span>
                </div>
            </td>
            <td>
                <span class="total">${productPrice.toLocaleString('vi-VN')} đ</span>
            </td>
            <td class="text-center">
                <input type="checkbox" name="stockoutdetail_set-${formIndex}-DELETE" style="display: none;">
                <i class="bi bi-x-lg delete-row"></i>
            </td>
        `;
        tableBody.appendChild(newRow);

        const totalForms = document.querySelector('#id_stockoutdetail_set-TOTAL_FORMS');
        totalForms.value = parseInt(totalForms.value) + 1;
        formIndex++;

        // Reset selects
        document.getElementById('category-select').value = '';
        document.getElementById('product-select').innerHTML = '<option value="">Chọn sản phẩm</option>';
        document.getElementById('product-select').disabled = true;
        document.getElementById('batch-select').innerHTML = '<option value="">Chọn lô sản phẩm</option>';
        document.getElementById('batch-select').disabled = true;
        document.getElementById('add-product-btn').disabled = true;

        updateRowTotals();
        updateSummary();
    }
});

document.addEventListener('click', function(event) {
    if (event.target.classList.contains('delete-row')) {
        const row = event.target.closest('tr');
        const deleteInput = row.querySelector('input[name$="-DELETE"]');
        if (deleteInput) {
            deleteInput.checked = true;
            row.style.display = 'none';
        } else {
            row.remove();
        }
        updateSummary();

        const visibleRows = document.querySelectorAll('.product-row:not([style*="display: none"])');
        if (visibleRows.length === 0) {
            const table = document.querySelector('.table');
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
});

function updateRowTotals() {
    document.querySelectorAll('.product-row:not([style*="display: none"])').forEach(row => {
        const quantity = parseFloat(row.querySelector('.quantity').value) || 0;
        const priceElement = row.querySelector('.price');
        const price = parseFloat(priceElement.dataset.price) || 0;
        const discount = parseFloat(row.querySelector('.discount').value) || 0;
        const total = quantity * price * (1 - discount / 100);
        row.querySelector('.total').textContent = total.toLocaleString('vi-VN') + ' đ';
    });
}

document.addEventListener('input', function(event) {
    if (event.target.classList.contains('quantity') || event.target.classList.contains('discount')) {
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
    let totalItems = 0;
    let totalAmount = 0;
    let totalDiscount = 0;

    document.querySelectorAll('.product-row:not([style*="display: none"])').forEach(row => {
        const quantity = parseFloat(row.querySelector('.quantity').value) || 0;
        const priceElement = row.querySelector('.price');
        const price = parseFloat(priceElement.dataset.price) || 0;
        const discount = parseFloat(row.querySelector('.discount').value) || 0;
        const total = quantity * price * (1 - discount / 100);

        totalItems += quantity;
        totalAmount += quantity * price;
        totalDiscount += quantity * price * (discount / 100);
    });

    const finalAmount = totalAmount - totalDiscount;
    const amountPaidInput = document.querySelector('.amount-paid');
    const amountPaid = amountPaidInput ? (parseFloat(amountPaidInput.value) || 0) : 0;
    const remainingDebt = finalAmount - amountPaid;

    const totalItemsElement = document.querySelector('.summary-box .total-items');
    const totalAmountElement = document.querySelector('.summary-box .total-amount');
    const totalDiscountElement = document.querySelector('.summary-box .total-discount');
    const finalAmountElement = document.querySelector('.summary-box .final-amount');
    const amountPaidDisplayElement = document.querySelector('.summary-box .amount-paid-display');
    const remainingDebtElement = document.querySelector('.summary-box .remaining-debt');
    const actualReceivedElement = document.querySelector('.summary-box .actual-received');

    if (totalItemsElement) totalItemsElement.textContent = totalItems;
    if (totalAmountElement) totalAmountElement.textContent = totalAmount.toLocaleString('vi-VN') + ' đ';
    if (totalDiscountElement) totalDiscountElement.textContent = totalDiscount.toLocaleString('vi-VN') + ' đ';
    if (finalAmountElement) finalAmountElement.textContent = finalAmount.toLocaleString('vi-VN') + ' đ';
    if (amountPaidDisplayElement) amountPaidDisplayElement.textContent = amountPaid.toLocaleString('vi-VN') + ' đ';
    if (remainingDebtElement) remainingDebtElement.textContent = remainingDebt.toLocaleString('vi-VN') + ' đ';
    if (actualReceivedElement) actualReceivedElement.textContent = amountPaid.toLocaleString('vi-VN') + ' đ';
}

document.addEventListener('DOMContentLoaded', function() {
    updateRowTotals();
    updateSummary();
});
