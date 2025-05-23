// your_project_root/static/js/admin_profile_actions.js
console.log("admin_commission_popup.js loaded and running!");
(function($) { // Encapsulate with jQuery wrapper for safety
    document.addEventListener('DOMContentLoaded', function() {
        const actionInput = document.getElementById('action_input');
        const approveButton = document.querySelector('button[name="_approve_teacher"]');
        const rejectButton = document.querySelector('button[name="_reject_teacher"]');
        
        // Get references to the form fields for validation
        const commissionField = document.getElementById('id_commission_percentage');
        const rejectionReasonField = document.getElementById('id_rejection_reason');

        // Event listener for the Approve button
        if (approveButton) {
            approveButton.addEventListener('click', function(event) {
                actionInput.value = 'approve_teacher'; // Set the hidden action field
                
                // Client-side validation for commission percentage
                if (commissionField) {
                    const commissionValue = parseFloat(commissionField.value);
                    if (isNaN(commissionValue) || commissionValue < 0 || commissionValue > 100) {
                        alert("Please enter a valid commission percentage between 0 and 100 before approving.");
                        event.preventDefault(); // Prevent form submission
                        return; // Stop further execution
                    }
                }
                // Optional: You could make rejection_reason blank if approving
                if (rejectionReasonField) {
                    rejectionReasonField.value = '';
                }
            });
        }

        // Event listener for the Reject button
        if (rejectButton) {
            rejectButton.addEventListener('click', function(event) {
                actionInput.value = 'reject_teacher'; // Set the hidden action field
                
                // Client-side validation for rejection reason
                if (rejectionReasonField) {
                    if (rejectionReasonField.value.trim() === "") {
                        alert("Please enter a reason for rejection.");
                        event.preventDefault(); // Prevent form submission
                        return; // Stop further execution
                    }
                }
                // Optional: Set commission to 0 if rejecting, for clarity in the UI
                if (commissionField) {
                    commissionField.value = "0.00";
                }
            });
        }

        // IMPORTANT: Ensure the action input is cleared on standard form submission (e.g., clicking 'Save')
        // if the custom buttons were NOT used. This prevents accidental re-triggering of actions.
        const form = document.querySelector('#content-main form');
        if (form) {
            form.addEventListener('submit', function(event) {
                // If the action input value is not set by our custom buttons, ensure it's empty
                // This means a standard 'Save' was clicked, not 'Approve'/'Reject'
                if (event.submitter && !event.submitter.name.startsWith('_approve_teacher') && !event.submitter.name.startsWith('_reject_teacher')) {
                     actionInput.value = '';
                }
            });
        }
    });
})(django.jQuery); // Pass django.jQuery if you want to use Django's bundled jQuery instance