
// ========================================
// 1. API CONFIGURATION
// ========================================

const API_URL = window.location.origin;

// Store documents returned by the backend.
let allDocuments = [];


// ========================================
// 2. INITIALIZE FRONTEND
// ========================================

document.addEventListener("DOMContentLoaded", () => {

    loadDocuments();

    initializeDocumentFilters();

    initializeMobileNavigation();

    // Load PostgreSQL database monitoring
    loadDatabaseMonitoring();

});


// ========================================
// 3. DOCUMENT SEARCH AND FILTER
// ========================================

function initializeDocumentFilters() {

    const searchInput = document.getElementById("documentSearch");

    const statusFilter = document.getElementById("statusFilter");

    searchInput.addEventListener("input", renderDocuments);

    statusFilter.addEventListener("change", renderDocuments);

}


function renderDocuments() {

    const tableBody = document.getElementById("documentTableBody");

    const searchInput = document.getElementById("documentSearch");

    const statusFilter = document.getElementById("statusFilter");

    const resultCount = document.getElementById("documentResultCount");


    const searchTerm = searchInput.value.trim().toLowerCase();

    const selectedStatus = statusFilter.value;


    const filteredDocuments = allDocuments.filter(doc => {

        const filenameMatches = (doc.filename || "")
            .toLowerCase()
            .includes(searchTerm);

        const statusMatches =
            selectedStatus === "all" ||
            doc.status === selectedStatus;

        return filenameMatches && statusMatches;

    });


    resultCount.textContent =
        `Showing ${filteredDocuments.length} of ${allDocuments.length} documents`;


    tableBody.replaceChildren();


    if (filteredDocuments.length === 0) {

        const row = document.createElement("tr");

        const cell = document.createElement("td");

        cell.colSpan = 5;

        cell.className = "empty-message";

        cell.textContent = allDocuments.length === 0
            ? "No documents uploaded yet."
            : "No documents match your search or filter.";

        row.appendChild(cell);

        tableBody.appendChild(row);

        return;

    }


    filteredDocuments.forEach(doc => {

        const row = document.createElement("tr");


        // Filename
        const filenameCell = document.createElement("td");

        filenameCell.textContent = "📄 " + doc.filename;


        // Status
        const statusCell = document.createElement("td");

        const statusBadge = document.createElement("span");

        const allowedStatuses = [
            "processed",
            "processing",
            "failed"
        ];

        statusBadge.className =
            "status-badge status-" +
            (allowedStatuses.includes(doc.status)
                ? doc.status
                : "other");

        statusBadge.textContent = doc.status || "Unknown";

        statusCell.appendChild(statusBadge);


        // Chunks
        const chunksCell = document.createElement("td");

        chunksCell.textContent = doc.total_chunks ?? 0;


        // Upload date
        const dateCell = document.createElement("td");

        const uploadDate = new Date(doc.created_at);

        dateCell.textContent = Number.isNaN(uploadDate.getTime())
            ? "Not available"
            : uploadDate.toLocaleString();


        // View details
        const actionCell = document.createElement("td");

        const viewButton = document.createElement("button");

        viewButton.type = "button";

        viewButton.className = "view-btn";

        viewButton.textContent = "View Details";


        viewButton.addEventListener("click", () => {

            viewDocumentDetails(doc.document_id);

        });


        actionCell.appendChild(viewButton);


        row.append(
            filenameCell,
            statusCell,
            chunksCell,
            dateCell,
            actionCell
        );


        tableBody.appendChild(row);

    });

}


// ========================================
// 4. LOAD DOCUMENTS
// ========================================

async function loadDocuments(preferredDocumentId = null) {

    const select = document.getElementById("documentSelect");

    const tableBody = document.getElementById("documentTableBody");


    try {

        const previousSelection = preferredDocumentId || select.value;


        const response = await fetch(
            `${API_URL}/documents/list`
        );

        const result = await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail || "Unable to load documents."
            );

        }


        allDocuments = result.documents || [];


        // Dashboard counts
        document.getElementById("totalDocuments").textContent =
            result.total_documents ?? allDocuments.length;


        const processedCount = allDocuments.filter(
            doc => doc.status === "processed"
        ).length;


        document.getElementById("processedDocuments").textContent =
            processedCount;


        // Render searchable document table
        renderDocuments();


        // Populate AI document dropdown
        select.replaceChildren();


        const allOption = document.createElement("option");

        allOption.value = "all";

        allOption.textContent = "All Documents";

        select.appendChild(allOption);


        allDocuments
            .filter(doc => doc.status === "processed")
            .forEach(doc => {

                const option = document.createElement("option");

                option.value = doc.document_id;

                option.textContent =
                    `${doc.filename} (${doc.total_chunks} chunks)`;

                select.appendChild(option);

            });


        // Restore previous selection if available
        const selectionExists = Array.from(select.options).some(
            option => option.value === previousSelection
        );


        select.value = selectionExists
            ? previousSelection
            : "all";


    } catch (error) {

        console.error("Document loading error:", error);


        tableBody.replaceChildren();


        const row = document.createElement("tr");

        const cell = document.createElement("td");

        cell.colSpan = 5;

        cell.className = "empty-message";

        cell.textContent =
            "Unable to load documents: " + error.message;


        row.appendChild(cell);

        tableBody.appendChild(row);


        document.getElementById("documentResultCount").textContent =
            "Unable to load documents";


        select.replaceChildren();


        const option = document.createElement("option");

        option.value = "";

        option.textContent = "Unable to load documents";

        select.appendChild(option);

    }

}


// ========================================
// 5. UPLOAD PDF
// ========================================

async function uploadDocument() {

    const fileInput = document.getElementById("pdfFile");

    const uploadBtn = document.getElementById("uploadBtn");

    const status = document.getElementById("uploadStatus");

    const documentInfo = document.getElementById("documentInfo");


    const file = fileInput.files[0];


    if (!file) {

        status.textContent = "Please select a PDF file.";

        return;

    }


    if (!file.name.toLowerCase().endsWith(".pdf")) {

        status.textContent = "Only PDF files are supported.";

        return;

    }


    if (file.size > 20 * 1024 * 1024) {

        status.textContent = "PDF file must not exceed 20 MB.";

        return;

    }


    const formData = new FormData();

    formData.append("file", file);


    uploadBtn.disabled = true;

    status.textContent = "Uploading and processing PDF...";

    documentInfo.textContent = "";


    try {

        const response = await fetch(
            `${API_URL}/documents/upload`,
            {
                method: "POST",
                body: formData
            }
        );


        const result = await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail || "Upload failed."
            );

        }


        status.textContent = result.message;


        documentInfo.textContent =
            `Filename: ${result.filename} | ` +
            `Chunks: ${result.total_chunks} | ` +
            `Status: ${result.status}`;


        await loadDocuments(result.document_id);


        // Clear document search and status filters
        document.getElementById("documentSearch").value = "";

        document.getElementById("statusFilter").value = "all";

        renderDocuments();


        // Refresh database monitoring after upload
        await loadDatabaseMonitoring();


        fileInput.value = "";


    } catch (error) {

        status.textContent = "Error: " + error.message;

        console.error("Upload error:", error);


    } finally {

        uploadBtn.disabled = false;

    }

}


// ========================================
// 6. VIEW DOCUMENT DETAILS
// ========================================

async function viewDocumentDetails(documentId) {

    const detailsDiv = document.getElementById("documentDetails");

    detailsDiv.textContent = "Loading document details...";


    try {

        const response = await fetch(
            `${API_URL}/documents/details/${encodeURIComponent(documentId)}`
        );


        const result = await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail || "Unable to retrieve document details."
            );

        }


        detailsDiv.replaceChildren();


        const card = document.createElement("div");

        card.className = "details-card";


        const heading = document.createElement("h3");

        heading.textContent = "Document Details";

        card.appendChild(heading);


        function addDetail(label, value) {

            const paragraph = document.createElement("p");

            const strong = document.createElement("strong");

            strong.textContent = label + ": ";


            paragraph.appendChild(strong);

            paragraph.appendChild(
                document.createTextNode(value ?? "Not available")
            );


            card.appendChild(paragraph);

        }


        addDetail("Filename", result.filename);

        addDetail("Content Type", result.content_type);

        addDetail("File Size", `${result.file_size} bytes`);

        addDetail("Status", result.status);

        addDetail("Total Chunks", result.total_chunks);


        const createdDate = new Date(result.created_at);


        addDetail(
            "Uploaded Date",
            Number.isNaN(createdDate.getTime())
                ? "Not available"
                : createdDate.toLocaleString()
        );


        const chunkHeading = document.createElement("h3");

        chunkHeading.textContent = "Document Text Chunks";

        card.appendChild(chunkHeading);


        if (!result.chunks || result.chunks.length === 0) {

            const message = document.createElement("p");

            message.textContent = "No chunks found.";

            card.appendChild(message);


        } else {

            result.chunks.forEach(chunk => {

                const chunkBox = document.createElement("div");

                chunkBox.className = "chunk-item";


                const chunkTitle = document.createElement("h4");

                chunkTitle.textContent =
                    `Chunk ${chunk.chunk_index}`;


                const chunkContent = document.createElement("p");

                chunkContent.textContent =
                    chunk.content_preview || "No preview available.";


                chunkBox.append(chunkTitle, chunkContent);

                card.appendChild(chunkBox);

            });

        }


        detailsDiv.appendChild(card);


        detailsDiv.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


    } catch (error) {

        detailsDiv.textContent =
            "Error loading document details: " + error.message;

        console.error("Document details error:", error);

    }

}


// ========================================
// 7. ASK AI QUESTION
// ========================================

async function askQuestion() {

    const questionInput = document.getElementById("question");

    const documentSelect = document.getElementById("documentSelect");

    const askBtn = document.getElementById("askBtn");

    const loading = document.getElementById("loading");

    const answerSection = document.getElementById("answerSection");

    const answerDiv = document.getElementById("answer");

    const sourcesDiv = document.getElementById("sources");


    const question = questionInput.value.trim();

    const selectedDocument = documentSelect.value;


    if (!selectedDocument) {

        alert("Please select a document or All Documents.");

        return;

    }


    if (!question) {

        alert("Please enter your question.");

        return;

    }


    const documentId =
        selectedDocument === "all" ? null : selectedDocument;


    askBtn.disabled = true;


    loading.textContent = documentId === null
        ? "Searching all documents and generating answer..."
        : "Searching selected document and generating answer...";


    answerSection.style.display = "none";

    answerDiv.textContent = "";

    sourcesDiv.replaceChildren();


    try {

        const response = await fetch(
            `${API_URL}/documents/ask`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    question: question,
                    top_k: 3,
                    document_id: documentId
                })

            }
        );


        const result = await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail || "Question processing failed."
            );

        }


        answerDiv.textContent =
            result.answer || "No answer was returned.";


        // Display retrieved sources
        const sources = result.sources || [];


        sources.forEach((source, index) => {

            const item = document.createElement("div");

            item.className = "source-item";


            // Source ID
            const sourceTitle = document.createElement("strong");

            sourceTitle.textContent =
                source.source_id || `S${index + 1}`;


            // Filename and metadata
            const metadata = document.createElement("p");

            metadata.textContent =
                `File: ${source.filename} | ` +
                `Chunk: ${source.chunk_index} | ` +
                `Similarity: ${source.similarity}`;


            item.append(sourceTitle, metadata);


            // Relevant content preview
            if (source.content_preview) {

                const preview = document.createElement("p");

                preview.className = "source-preview";

                preview.textContent = source.content_preview;

                item.appendChild(preview);

            }


            sourcesDiv.appendChild(item);

        });


        if (sources.length === 0) {

            sourcesDiv.textContent = "No matching sources found.";

        }


        answerSection.style.display = "block";

        loading.textContent = "";


        answerSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


    } catch (error) {

        loading.textContent = "Error: " + error.message;

        console.error("Ask question error:", error);


    } finally {

        askBtn.disabled = false;

    }

}


// ========================================
// 8. MOBILE SIDEBAR NAVIGATION
// ========================================

function initializeMobileNavigation() {

    const sidebar = document.getElementById("sidebar");

    const overlay = document.getElementById("sidebarOverlay");

    const menuToggle = document.getElementById("menuToggle");

    const navLinks = document.querySelectorAll(
        ".sidebar-nav .nav-item"
    );


    function openMenu() {

        sidebar.classList.add("mobile-open");

        overlay.classList.add("visible");

        menuToggle.setAttribute("aria-expanded", "true");

        document.body.classList.add("menu-open");

    }


    function closeMenu() {

        sidebar.classList.remove("mobile-open");

        overlay.classList.remove("visible");

        menuToggle.setAttribute("aria-expanded", "false");

        document.body.classList.remove("menu-open");

    }


    menuToggle.addEventListener("click", () => {

        const isOpen = sidebar.classList.contains("mobile-open");


        if (isOpen) {

            closeMenu();

        } else {

            openMenu();

        }

    });


    overlay.addEventListener("click", closeMenu);


    navLinks.forEach(link => {

        link.addEventListener("click", () => {

            navLinks.forEach(item =>
                item.classList.remove("active")
            );

            link.classList.add("active");

            closeMenu();

        });

    });


    // Close mobile sidebar when returning to desktop width
    window.addEventListener("resize", () => {

        if (window.innerWidth > 760) {

            closeMenu();

        }

    });


    // Close sidebar using Escape key
    document.addEventListener("keydown", event => {

        if (event.key === "Escape") {

            closeMenu();

        }

    });

}


// ========================================
// 9. POSTGRESQL DATABASE MONITORING
// ========================================

async function loadDatabaseMonitoring() {

    const refreshBtn = document.getElementById(
        "refreshMonitoringBtn"
    );

    const statusMessage = document.getElementById(
        "monitoringStatus"
    );

    const updatedAt = document.getElementById(
        "monitoringUpdatedAt"
    );


    if (refreshBtn) {

        refreshBtn.disabled = true;

        refreshBtn.textContent = "Loading...";

    }


    if (statusMessage) {

        statusMessage.textContent =
            "Loading PostgreSQL monitoring information...";

    }


    try {

        const response = await fetch(
            `${API_URL}/monitoring/database`
        );


        const result = await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail ||
                "Unable to load database monitoring."
            );

        }


        if (result.status !== "connected") {

            throw new Error(
                result.error || "Database is disconnected."
            );

        }


        // ------------------------------------
        // DATABASE OVERVIEW
        // ------------------------------------

        document.getElementById("dbStatus").textContent =
            "Connected";


        document.getElementById("dbName").textContent =
            result.database.name;


        document.getElementById("dbSize").textContent =
            result.database.size;


        // ------------------------------------
        // DOCUMENT STATISTICS
        // ------------------------------------

        document.getElementById("monitorDocuments").textContent =
            result.documents.total;


        document.getElementById(
            "monitorProcessedDocuments"
        ).textContent =
            `Processed: ${result.documents.processed}`;


        document.getElementById("monitorChunks").textContent =
            result.chunks.total;


        document.getElementById("monitorEmbeddings").textContent =
            `Embeddings: ${result.chunks.embeddings}`;


        // ------------------------------------
        // DATABASE HEALTH
        // ------------------------------------

        const version = result.database.version || "Not available";


        document.getElementById("dbVersion").textContent =
            version.split(" on ")[0];


        document.getElementById("activeConnections").textContent =
            result.connections.active;


        document.getElementById("totalConnections").textContent =
            `Total: ${result.connections.total} / ${result.connections.maximum}`;


        document.getElementById("missingEmbeddings").textContent =
            result.chunks.missing_embeddings;


        document.getElementById("monitoringQueryTime").textContent =
            `${result.monitoring_query_time_seconds} s`;


        // ------------------------------------
        // STORAGE INFORMATION
        // ------------------------------------

        document.getElementById("documentsTableSize").textContent =
            result.storage.documents_table;


        document.getElementById("chunksTableSize").textContent =
            result.storage.chunks_table;


        // ------------------------------------
        // MONITORING STATUS
        // ------------------------------------

        statusMessage.textContent =
            "Database monitoring information loaded successfully.";


        updatedAt.textContent =
            `Last updated: ${new Date().toLocaleString()}`;


    } catch (error) {

        console.error("Database monitoring error:", error);


        document.getElementById("dbStatus").textContent =
            "Disconnected";


        statusMessage.textContent =
            "Monitoring error: " + error.message;


    } finally {

        if (refreshBtn) {

            refreshBtn.disabled = false;

            refreshBtn.textContent = "↻ Refresh Monitoring";

        }

    }

}


// ========================================
// 10. EXPOSE HTML BUTTON FUNCTIONS
// ========================================

window.uploadDocument = uploadDocument;

window.loadDocuments = loadDocuments;

window.askQuestion = askQuestion;

window.viewDocumentDetails = viewDocumentDetails;

window.loadDatabaseMonitoring = loadDatabaseMonitoring;
