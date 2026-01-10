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

            fetch("{{ url_for('static', filename='data/municipalities.json') }}")
                .then(response => response.json())
                .then(data => {
                    leyteData = data;
                    populateMunicipalities();
                })
                .catch(error => console.error("Error loading JSON:",error))

            fetch("{{ url_for('static', filename='data/barangays.json') }}")
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

            form.addEventListener('submit', async function (event) {
                // Prevent default submission behavior
                event.preventDefault()
                event.stopPropagation()

                // // Check if the form is valid according to HTML5/Bootstrap validation
                if (!form.checkValidity()) {
                    form.classList.add('was-validated');
                    return; // Stop if validation fails
                }
                
                // // --- Form is valid, proceed with data collection and submission ---

                const patientIsMemberValue = document.querySelector('input[name="patientIsMember"]:checked').value;

                const data = {
                    pin: form.pin.value,
                    lastName: form.lastName.value,
                    firstName: form.firstName.value,
                    nameExt: form.nameExt.value,
                    middleName: form.middleName.value,
                    dob: form.dob.value,
                    sex: form.sex.value,
                    street: form.street.value,
                    barangay: form.barangay.value,
                    municipality: form.municipality.value,
                    mobile: form.mobile.value,
                    email: form.email.value,
                    patientIsMember: patientIsMemberValue,
                    dependent: patientIsMemberValue === "no" ? {
                        depPin: form.depPin.value,
                        depLname: form.depLname.value,
                        depFname: form.depFname.value,
                        depMname: form.depMname.value,
                        depDob: form.depDob.value,
                        depSex: form.depSex.value,
                        depExt: form.depExt.value,
                        relationship: form.relationship.value
                    } : null,
                    signee: form.signee.value,
                    representative: form.signee.value === "representative" ? {
                        repName: form.repName.value,
                        repRelationship: form.repRelationship.value,
                        repReason: form.repReason.value
                    } : null,
                    patientDisposition: form.querySelector("select[name='patientDisposition']")?.value || ""
                };
                
                // // ** NEW SUBMISSION VIA FETCH API TO /submit_form **
                // try {
                //     console.log("Attempting to submit data to /submit_form:", data);
                    
                //     const response = await fetch('/submit_form', {
                //         method: 'POST',
                //         headers: {
                //             'Content-Type': 'application/json'
                //         },
                //         // Convert the JavaScript object to a JSON string
                //         body: JSON.stringify(data)
                //     });

                //     if (response.ok) {
                //         // Submission was successful (e.g., status 200-299)
                //         alert("✅ MHO Burauen Form submitted successfully!");
                //         window.location.href = '/view_print';
                //         form.reset(); // Clear the form fields
                //         form.classList.remove('was-validated'); // Remove validation state
                //     } else {
                //         // Submission failed on the server side (e.g., status 400 or 500)
                //         const errorText = await response.text();
                //         console.error("Submission failed:", errorText);
                //         alert(`⚠️ Submission failed. Server responded with status: ${response.status}`);
                //     }
                // } catch (error) {
                //     // Network error (e.g., server offline)
                //     console.error("Network or unexpected error during submission:", error);
                //     alert("❌ An error occurred. Could not connect to the submission server.");
                // }
                console.log("Test");
            });
                function hideLoader(tabId) {
    const loader = document.getElementById(`loader-${tabId}`);
    const iframe = loader.nextElementSibling;

    loader.style.display = "none";
    iframe.classList.remove("d-none");
}