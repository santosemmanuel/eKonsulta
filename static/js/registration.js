
  // ====== Receive data from backend (DO NOT ALTER) ======


// DOM elements

let leyteData = {};
let leyteBrgy = {};

fetch("static/data/municipalities.json")
    .then(response => response.json())
    .then(data => {
        leyteData = data;
        populateMunicipalities();
    })
    .catch(error => console.error("Error loading JSON:",error))

fetch("static/data/barangays.json")
    .then(response => response.json())
    .then(data => {
        leyteBrgy = data;
    })
    .catch(error => console.error("Error loading JSON:",error))

function populateMunicipalities(){
    const municipalitySelect = document.getElementById("municipality");

    for(let iteration in leyteData){
        const option = document.createElement('option');
        option.value = leyteData[iteration].name
        option.text = leyteData[iteration].name
        municipalitySelect.appendChild(option);
    }

}



document.getElementById('municipality').addEventListener("change", function () {
    const barangaySelect = document.getElementById("barangay");
    barangaySelect.innerHTML = '<option value="">-- Select Barangay --</option>';
    const selectedMunicipality = this.value;
    const filterBrgy = leyteBrgy.filter(
        item => item.citymun === selectedMunicipality
    )

    filterBrgy.forEach( brgy => {
        const option = document.createElement("option");
        option.value = brgy.name
        option.text = brgy.name
        barangaySelect.appendChild(option)
    })

})

const registrationform = document.getElementById('cecregistrationForm')

const toggleBoxes = document.querySelectorAll('input[name="patientIsMember"]');
const dependentPINDiv = document.getElementById('DependentPIN');
toggleBoxes.forEach(box => {
    box.addEventListener("change", function() {
        dependentPINDiv?.classList.toggle('d-none', this.value !== 'dependent');
    })
});

function isVisible(el) {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
}

function clearErrors(form) {
    form.querySelectorAll(".is-invalid").forEach(el => el.classList.remove("is-invalid"));
}

function invalidate(field, message) {
    field.classList.add("is-invalid");

    let feedback = field.parentElement.querySelector(".invalid-feedback");
    if (!feedback) {
        feedback = document.createElement("div");
        feedback.className = "invalid-feedback";
        field.parentElement.appendChild(feedback);
    }
    feedback.innerText = message;

    field.focus();
}

    
document.addEventListener("DOMContentLoaded", function () {

    const dobInput = document.querySelector('input[name="dob"]');
    const repInput = document.querySelector('#repGuardianDiv');
    const relationshipInput = document.querySelector('#relationshipDiv');

    function calculateAge(dob) {
        const today = new Date();
        const birthDate = new Date(dob);

        let age = today.getFullYear() - birthDate.getFullYear();
        const m = today.getMonth() - birthDate.getMonth();

        if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }

        return age;
    }

    function toggleRepresentative() {
        if (!dobInput.value) {
            repInput.style.display = "none";
            relationshipInput.style.display = "none";
            return;
        }

        const age = calculateAge(dobInput.value);

        if (age <= 21) {
            repInput.style.display = "block";
            relationshipInput.style.display = "block";
        } else {
            repInput.style.display = "none";
            relationshipInput.style.display = "none";

            // Clear values when hidden
            document.querySelector('input[name="RepOrGuardian"]').value = "";
            document.querySelector('select[name="relationship"]').value = "";
        }
    }

    // Run when DOB changes
    dobInput.addEventListener("input", toggleRepresentative);

    // Run on page load (in case value already exists)
    toggleRepresentative();


});

const relationshipSelect = document.getElementById("relationshipSelect");
const otherDiv = document.getElementById("otherRelationshipDiv");
const repDiv = document.getElementById("repGuardianDiv");
const relDiv = document.getElementById("relationshipDiv");

relationshipSelect.addEventListener("change", function () {

    if (this.value === "Others") {

        // Show Others input
        otherDiv.style.display = "block";

        // Adjust column sizes
        repDiv.classList.remove("col-md-8");
        repDiv.classList.add("col-md-6");

        relDiv.classList.remove("col-md-4");
        relDiv.classList.add("col-md-3");

    } else {

        // Hide Others input
        otherDiv.style.display = "none";

        // Restore original sizes
        repDiv.classList.remove("col-md-6");
        repDiv.classList.add("col-md-8");

        relDiv.classList.remove("col-md-3");
        relDiv.classList.add("col-md-4");
    }
});




function buildFormData(form) {
    const memberType = document.querySelector(
        "input[name='patientIsMember']:checked"
    ).value;

    const transactionNumber = form.transactionNumber?.value.trim() || "";
    const philhealthChecked = document.querySelector("#checkPhilhealth")?.checked || false;
    const philsysChecked = document.querySelector("#checkPhilsys")?.checked || false;

    return {
        patientIsMember: memberType,
        pin: form.pin.value.trim(),
        dependentPin:
            memberType === "dependent"
                ? form.dependentPin.value.trim()
                : "",

        personalInfo: {
            lastName: form.lastName.value.trim(),
            firstName: form.firstName.value.trim(),
            middleName: form.middleName.value.trim(),
            nameExt: form.nameExt.value.trim()
        },

        address: {
            municipality: form.municipality.value,
            barangay: form.barangay.value
        },

        otherDetails: {
            dob: form.dob.value,
            sex: form.sex.value,
            mobile: form.mobile.value,
            representative: form.RepOrGuardian.value.trim(),
            relationship: form.relationship.value,
            otherRelationship: form.other_relationship.value.trim()
        },
        
        transactionInfo: {
            transactionNumber: transactionNumber,
            philhealth: philhealthChecked,
            philsys: philsysChecked
        },
    };
}


function validateForm(form) {
    clearErrors(form);

    const fields = form.querySelectorAll("input, select, textarea");
    const transactionInput = form.querySelector('[name="transactionNumber"]');
    const philhealthChecked = form.querySelector('#checkPhilhealth')?.checked;
    const philsysChecked = form.querySelector('#checkPhilsys')?.checked;

    for (let field of fields) {

        // Skip personal info section
        if (field.closest(".personal-info") || field.name === "mobile") continue;

        // Skip hidden or disabled
        if (field.disabled || !isVisible(field)) continue;
        
        // ⭐ Skip Transaction Number in normal required check
        if (field.name === "transactionNumber") continue;


        // Required check
        if (!field.value || field.value.trim() === "") {
            invalidate(field, "This field is required.");
            return false;
        }

        // PIN validation
        if (["pin", "dependentPin"].includes(field.name)) {
            if (!/^(\d{1,2}-\d{9,10}-\d|\d{11,13})$/.test(field.value)) {
                invalidate(field, "PIN format must be XX-XXXXXXXXX-X or without dashes.");
                return false;
            }
        }
        // // Mobile number validation
        // if (field.name === "mobile") {
        //     if (!/^09\d{9}$/.test(field.value)) {
        //         invalidate(field, "Mobile must start with 09 and be 11 digits.");
        //         return false;
        //     }
        // }

        // Date validation
        if (field.type === "date") {
            const date = new Date(field.value);
            if (date > new Date()) {
                invalidate(field, "Date cannot be in the future.");
                return false;
            }
        }
    }

    if (philhealthChecked || philsysChecked) {
        if (!transactionInput.value || transactionInput.value.trim() === "") {
            invalidate(transactionInput,
                "Transaction Number is required when Philhealth or Philsys is checked."
            );
            return false;
        }

    }

    return true;
}

// async function loadPdfViewer() {
//     const tabNav = document.getElementById("pdfTabNav");
//     const tabContent = document.getElementById("pdfTabContent");

//     tabNav.innerHTML = "";
//     tabContent.innerHTML = "";

//     try {
//         const response = await fetch("/get_pdfs");
//         const pdfs = await response.json();

//         pdfs.forEach((pdf, index) => {
//             const tabId = `pdf-${index}`;
//             const isActive = index === 0 ? "active" : "";

//             // TAB BUTTON
//             tabNav.insertAdjacentHTML(
//                 "beforeend",
//                 `
//                 <li class="nav-item" role="presentation">
//                     <button class="nav-link ${isActive}"
//                         data-bs-toggle="pill"
//                         data-bs-target="#${tabId}">
//                         <i class="fa-solid fa-file-pdf"></i>
//                         ${pdf.name}
//                     </button>
//                 </li>
//                 `
//             );

//             // TAB CONTENT + LOADER + IFRAME
//             tabContent.insertAdjacentHTML(
//                 "beforeend",
//                 `
//                 <div class="tab-pane fade show ${isActive}" id="${tabId}" role="tabpanel">
                    
//                     <!-- Loader -->
//                     <div id="loader-${tabId}" class="text-center my-4">
//                         <div class="spinner-border text-primary"></div>
//                         <p class="mt-2">Loading PDF...</p>
//                     </div>

//                     <!-- PDF -->
//                     <iframe
//                         src="${pdf.url}?t=${Date.now()}"
//                         class="w-100 d-none pdf-frame"
//                         height="600"
//                         frameborder="0"
//                         onload="hideLoader('${tabId}')">
//                     </iframe>

//                 </div>
//                 `
//             );
//         });

//     } catch (err) {
//         console.error("Failed to load PDFs:", err);
//     }
// }

function showToast(type, message) {
  Swal.fire({
    toast: true,
    position: 'top-end',
    icon: type,
    title: message,
    showConfirmButton: false,
    timer: 4000,
    timerProgressBar: true,
    customClass: {
      popup: 'colored-toast'
    }
  });
}

function showSuccess(message) {
  showToast('success', message);
}

function showError(message) {
  showToast('error', message);
}

const pdfTab = document.getElementById("pdfButton");

pdfTab?.addEventListener("click", function() {
    showPdfModal(pdfFilePCSF);
})

registrationform.addEventListener("submit", async function(event) {
    const transferChecked = document.querySelector("#checkTransfer")?.checked || false;
    const PreviousPCC = registrationform.PreviousPCC?.value.trim() || "";
    
    event.preventDefault();
    event.stopPropagation();

    if (!validateForm(registrationform)) 
    {
        showError("Please Fill Up All Required Fields Correctly.");
        return;
    }

    const data = buildFormData(registrationform);

    let submissionType = "/submit_form"; // Default submission type
    let submissionData = data; // Default submission data

    if(valueFromGet != "second_encounter"){
        submissionType = "/submitCECRegistration";

        if (attachment.value === "with_attachment"){
            if (frontImage === null || backImage === null) {
                showError("Please upload all required images.");
                return;
            }
        } else {
            if (birthCertificateImage && birthCertificateImage === null) {
                showError("Please upload the birth certificate.");
                return;
            }
        }

        data.transfer = {
            transfer: transferChecked,
            previousPCC: PreviousPCC
        };

        submissionData = {
            data: data,
            front: frontImage,
            back: backImage,
            birthCertificate: birthCertificateImage,
            valueToSubmit: valueFromGet
        };

    
    }

    try {
        const response = await fetch(submissionType, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(submissionData)
        });
        
        if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            showError(result.message || "Failed to submit form.");
            return;
        }

        const result = await response.json().catch(() => ({}));
        console.log(result);
        if (result.success && result.pdf_url) {
            
            const pdfMap = {
                pcsf: "PCSF",
                fpe: "FPE",
                ekass_epress: "EKASS, EPRESS",
                mca_pdf: "MCA"
            };

            for (const [key, title] of Object.entries(pdfMap)) {
                if (result.pdf_url[key]) {
                    const element = document.querySelector(`[data-title="${title}"]`);

                    if (element) {
                        element.dataset.pdf = result.pdf_url[key];
                        showPdfModal(result.pdf_url[key]);
                    } else {
                        console.warn(`Element with data-title="${title}" not found.`);
                    }
                }
            }
            showSuccess(result.message || "Form submitted successfully.");
        }

        const depPIN = document.getElementById('DependentPIN');
        if (!depPIN.classList.contains('d-none')) {
            depPIN.classList.add('d-none');
        }
        registrationform.reset();
        frontImage = null;
        backImage = null;
        birthCertificateImage = null;
        

    } catch (err) {
        console.error("❌ Submission failed:", err);
        showError("Failed to submit form.");
    }
});

const modalElement = document.getElementById('pdfViewerModal');

modalElement?.addEventListener('hidden.bs.modal', function () {
    const pdfFrame = document.getElementById('pdfFrame');

    if (pdfFrame) {
        pdfFrame.src = ""; // Stop PDF loading
    }
});

// Function to show PDF modal
function showPdfModal(pdfUrl) {
    const pdfFrame = document.getElementById('pdfFrame');
    const pdfLoader = document.getElementById('pdfLoader');
    const modalElement = document.getElementById('pdfViewerModal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

    // 1. Reset display states and source
    pdfLoader.style.setProperty('display', 'flex', 'important');
    pdfFrame.style.display = 'none';
    pdfFrame.src = pdfUrl;

    // 2. Synchronize the tab highlights to match the URL loaded
    document.querySelectorAll('.pdf-tab').forEach(tab => {
        if (tab.getAttribute('data-pdf') === pdfUrl) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // 3. Open the modal window
    modal.show();

    // 4. Hide loader once iframe completes rendering
    pdfFrame.onload = function () {
        pdfLoader.classList.add("d-none")
        pdfFrame.style.display = 'block';
    };
}

// 5. CRITICAL: Add click handlers for switching tabs INSIDE the modal window
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.pdf-tab').forEach(tab => {
        tab.addEventListener('click', function (e) {
            e.preventDefault();
            
            const selectedPdfUrl = this.getAttribute('data-pdf');
            const pdfFrame = document.getElementById('pdfFrame');
            const pdfLoader = document.getElementById('pdfLoader');

            if (selectedPdfUrl) {
                // Trigger loading state inside frame
                pdfLoader.style.setProperty('display', 'flex', 'important');
                pdfFrame.style.display = 'none';
                
                // Update active tab visuals manually
                document.querySelectorAll('.pdf-tab').forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Load new file
                pdfFrame.src = selectedPdfUrl;
            }
        });
    });
});

// Print functionality
document.getElementById('printPdfBtn')?.addEventListener('click', function() {
    const pdfFrame = document.getElementById('pdfFrame');
    if (pdfFrame?.src) {
        pdfFrame.contentWindow.print();
    }
});

// Download functionality
document.getElementById('downloadPdfBtn').addEventListener('click', function() {
    const pdfFrame = document.getElementById('pdfFrame');
    if (pdfFrame.src) {
        const link = document.createElement('a');
        link.href = pdfFrame.src;
        link.download = 'PCSF_Form.pdf';
        link.click();
    }
});

function hideLoader(tabId) {
    const loader = document.getElementById(`loader-${tabId}`);
    const iframe = loader.nextElementSibling;

    loader.style.display = "none";
    iframe.classList.remove("d-none");

    
}

function formatDateForInput(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // months are 0-based
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// document.getElementById('checkPinBtn').addEventListener('click', function() {
//     const pin = document.getElementById('pinInput').value.trim();
//     if (!pin) {
//         toastr.error("Please enter a PIN")
//         return;
//     }

//     fetch(`/get_patient/${pin}`)
//         .then(response => response.json())
//         .then(data => {
//             if (data.exists) {
//                 // Fill personal info
//                 document.querySelector('input[name="lastName"]').value = data.last_name || '';
//                 document.querySelector('input[name="firstName"]').value = data.first_name || '';
//                 document.querySelector('input[name="middleName"]').value = data.middle_name || '';
//                 document.querySelector('input[name="nameExt"]').value = data.name_ext || '';
//                 // Fill other details
//                 document.querySelector('input[name="dob"]').value = formatDateForInput(data.date_of_birth);
//                 document.querySelector('input[name="mobile"]').value = data.mobile || '';
//                 document.querySelector('select[name="sex"]').value = data.sex || '';

//                 // ✅ Set Municipality
//                 const municipalitySelect = document.getElementById("municipality");
//                 municipalitySelect.value = data.municipality || '';

//                 // ✅ Trigger change so barangays are populated
//                 const event = new Event('change');
//                 municipalitySelect.dispatchEvent(event);

//                 // ✅ Set Barangay after population
//                 const barangaySelect = document.getElementById("barangay");
//                 barangaySelect.value = data.barangay || '';

//             } else {
//                 toastr.error("PIN not found")
//             }
//         })
//         .catch(err => console.error(err));
// });

const toggle = document.getElementById("featureToggle");

    toggle.addEventListener("change", async () => {
       
      try {
         const res = await fetch("/toggle", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled: toggle.checked })
        });

        const data = await res.json();
        console.log("Session updated:", data);
      } catch (err) {
        console.error("Toggle failed:", err);
      }
    });


