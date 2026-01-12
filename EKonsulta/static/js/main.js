  // ====== Receive data from backend (DO NOT ALTER) ======


        // DOM elements
        const tabNav = document.getElementById("pdfTabNav");
        const tabContent = document.getElementById("pdfTabContent");

        // ====== Dynamically render the tabs ======
        pdfFiles.forEach((file, index) => {
            const tabId = `tab-${index}`;
            const isActive = index === 0 ? "active" : "";
            const isShown = index === 0 ? "show active" : "";

            // --- Generate Tab Button ---
            tabNav.innerHTML += `
                 <li class="nav-item" role="presentation">
            <button class="nav-link ${isActive} d-flex align-items-center gap-2 px-3 py-2" id="${tabId}-tab" data-bs-toggle="tab" data-bs-target="#${tabId}" type="button" role="tab">
                <i class="fa-solid fa-file-pdf"></i>
                ${file.name}
            </button>
        </li>
            `;

            // --- Generate Tab Content ---
            tabContent.innerHTML += `
                <div class="tab-pane fade ${isShown}" id="${tabId}" role="tabpanel">

            <!-- LOADER -->
            <div class="pdf-loader" id="loader-${tabId}">
                <i class="fa-solid fa-spinner fa-spin"></i>
                <div class="mt-2">Loading PDF...</div>
            </div>

            <!-- PDF -->
            <iframe class="pdf-frame d-none" src="${file.url}" onload="hideLoader('${tabId}')">
            </iframe>

        </div>
            `;
        });

        // ===== Print Function (DO NOT ALTER) =====
        function printPDF(filePath) {
            const printWin = window.open(filePath);
            printWin.focus();
            printWin.print();
        }

         const toggleBoxes = document.querySelectorAll('.toggle-box input');
            const dependentPINDiv = document.getElementById('DependentPIN');
            toggleBoxes.forEach(box => {
                box.addEventListener("change", function() {
                    dependentPINDiv.classList.toggle('d-none');
                })
            });

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
            const form = document.getElementById('philhealthForm')

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


function buildFormData(form) {
    const memberType = document.querySelector(
        "input[name='patientIsMember']:checked"
    ).value;

    return {
        patientIsMember: memberType,

        pin: form.pin.value.trim(),
        dependentPin:
            memberType === "dependent"
                ? form.dependentPin.value.trim()
                : null,

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
            mobile: form.mobile.value
        }
    };
}


function validateForm(form) {
    clearErrors(form);

    const fields = form.querySelectorAll("input, select, textarea");

    for (let field of fields) {

        // Skip personal info section
        if (field.closest(".personal-info")) continue;

        // Skip hidden or disabled
        if (field.disabled || !isVisible(field)) continue;

        // Required check
        if (!field.value || field.value.trim() === "") {
            invalidate(field, "This field is required.");
            return false;
        }

        // PIN validation
        if (["pin", "dependentPin"].includes(field.name)) {
            if (!/^\d{4,}$/.test(field.value)) {
                invalidate(field, "PIN must be at least 4 digits.");
                return false;
            }
        }

        // Mobile number validation
        if (field.name === "mobile") {
            if (!/^09\d{9}$/.test(field.value)) {
                invalidate(field, "Mobile must start with 09 and be 11 digits.");
                return false;
            }
        }

        // Date validation
        if (field.type === "date") {
            const date = new Date(field.value);
            if (date > new Date()) {
                invalidate(field, "Date cannot be in the future.");
                return false;
            }
        }
    }

    return true;
}

async function loadPdfViewer() {
    const tabNav = document.getElementById("pdfTabNav");
    const tabContent = document.getElementById("pdfTabContent");

    tabNav.innerHTML = "";
    tabContent.innerHTML = "";

    try {
        const response = await fetch("/get_pdfs");
        const pdfs = await response.json();

        pdfs.forEach((pdf, index) => {
            const tabId = `pdf-${index}`;
            const isActive = index === 0 ? "active" : "";

            // TAB BUTTON
            tabNav.insertAdjacentHTML(
                "beforeend",
                `
                <li class="nav-item" role="presentation">
                    <button class="nav-link ${isActive}"
                        data-bs-toggle="pill"
                        data-bs-target="#${tabId}">
                        <i class="fa-solid fa-file-pdf"></i>
                        ${pdf.name}
                    </button>
                </li>
                `
            );

            // TAB CONTENT + LOADER + IFRAME
            tabContent.insertAdjacentHTML(
                "beforeend",
                `
                <div class="tab-pane fade show ${isActive}" id="${tabId}" role="tabpanel">
                    
                    <!-- Loader -->
                    <div id="loader-${tabId}" class="text-center my-4">
                        <div class="spinner-border text-primary"></div>
                        <p class="mt-2">Loading PDF...</p>
                    </div>

                    <!-- PDF -->
                    <iframe
                        src="${pdf.url}?t=${Date.now()}"
                        class="w-100 d-none pdf-frame"
                        height="600"
                        frameborder="0"
                        onload="hideLoader('${tabId}')">
                    </iframe>

                </div>
                `
            );
        });

    } catch (err) {
        console.error("Failed to load PDFs:", err);
    }
}


          form.addEventListener("submit", async function (event) {
    event.preventDefault();
    event.stopPropagation();

    if (!validateForm(form)) 
    {
    
         return;
    }

    const data = buildFormData(form);

    try {
        const response = await fetch("/submit_form", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error("Server error");
        } else {
            await loadPdfViewer();
        }

        // const result = await response.json();
        // console.log("✅ Server response:", result);

        // alert("Form submitted successfully!");
        form.reset();

    } catch (err) {
        console.error("❌ Submission failed:", err);
        alert("Failed to submit form.");
    }
});



                function hideLoader(tabId) {
    const loader = document.getElementById(`loader-${tabId}`);
    const iframe = loader.nextElementSibling;

    loader.style.display = "none";
    iframe.classList.remove("d-none");

    
}