document.addEventListener('DOMContentLoaded', function() {
    function toggleSubscriptionField() {
        var typeField = document.getElementById('id_type');
        var subscriptionField = document.querySelector('.form-row.field-subscription');
        var discountField = document.querySelector('.form-row.field-discount_amount');
        if (!typeField || !subscriptionField) return;
        if (typeField.value === 'option1') {
            subscriptionField.style.display = '';
            discountField.style.display = 'none';
        } else {
            subscriptionField.style.display = 'none';
            discountField.style.display = '';
        }
    }
    var typeField = document.getElementById('id_type');
    if (typeField) {
        typeField.addEventListener('change', toggleSubscriptionField);
        toggleSubscriptionField();
    }
});