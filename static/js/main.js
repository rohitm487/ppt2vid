// Initialize variables
let processingId = null;
let selectedFiles = [];

// Initialize Google Sign-In
window.onload = function () {
    google.accounts.id.initialize({
        client_id: document.querySelector('#g_id_onload').getAttribute('data-client_id'),
        callback: handleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true
    });
    
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
        loadUserProfile();
        showMainContent();
    } else {
        showAuthSection();
    }
};

function handleCredentialResponse(response) {
    console.log('Google Sign-In response received');
    
    fetch('/api/auth/google', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            credential: response.credential
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.detail || 'Failed to authenticate');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Authentication successful');
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        loadUserProfile();
        showMainContent();
    })
    .catch(error => {
        console.error('Authentication error:', error);
        showMessage(error.message || 'Failed to sign in. Please try again.', 'error');
        showAuthSection();
    });
}

function loadUserProfile() {
    console.log('Loading user profile...');
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
        document.getElementById('userMenu').classList.remove('hidden');
        document.getElementById('userAvatar').src = user.picture;
        document.getElementById('userName').textContent = user.name;
        
        // Load user features
        fetch('/api/user/features', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load user features');
            }
            return response.json();
        })
        .then(features => {
            // Update subscription display
            document.getElementById('userPlan').innerHTML = `
                <span class="font-medium ${features.subscription_tier === 'PREMIUM' ? 'text-indigo-600' : 'text-gray-600'}">
                    ${features.subscription_tier.charAt(0) + features.subscription_tier.slice(1).toLowerCase()} Plan
                </span>
                <span class="text-xs text-gray-500 block">
                    ${features.limits.max_videos_per_day === Infinity ? 'Unlimited' : features.limits.max_videos_per_day} videos/day
                </span>
            `;
            
            // Store features for later use
            localStorage.setItem('userFeatures', JSON.stringify(features));
            
            // Update UI based on features
            updateUIBasedOnFeatures(features);
        })
        .catch(error => {
            console.error('Error loading user features:', error);
            showMessage('Failed to load user features', 'error');
        });
    } else {
        showAuthSection();
        showMessage('Failed to load user profile. Please sign in again.');
    }
}

function updateUIBasedOnFeatures(features) {
    // Update video quality info
    const videoQualityInfo = document.createElement('div');
    videoQualityInfo.className = 'text-sm text-gray-500 mt-2';
    videoQualityInfo.innerHTML = `
        <span class="font-medium">Video Quality:</span> 
        ${features.features.includes('hd_quality') ? 'HD (1920p)' : 'Standard (1280p)'}
    `;
    
    // Update slides limit info
    const slidesLimitInfo = document.createElement('div');
    slidesLimitInfo.className = 'text-sm text-gray-500 mt-1';
    slidesLimitInfo.innerHTML = `
        <span class="font-medium">Max Slides:</span> 
        ${features.limits.max_slides_per_video} per video
    `;
    
    // Update video duration info
    const durationInfo = document.createElement('div');
    durationInfo.className = 'text-sm text-gray-500 mt-1';
    durationInfo.innerHTML = `
        <span class="font-medium">Max Duration:</span> 
        ${Math.floor(features.limits.max_video_duration / 60)} minutes
    `;
    
    // Add feature badges
    const featureBadges = document.createElement('div');
    featureBadges.className = 'flex flex-wrap gap-2 mt-3';
    
    const badges = {
        'custom_scripts': 'Custom Scripts',
        'hd_quality': 'HD Quality',
        'background_music': 'Background Music'
    };
    
    for (const [feature, label] of Object.entries(badges)) {
        if (features.features.includes(feature)) {
            const badge = document.createElement('span');
            badge.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800';
            badge.textContent = label;
            featureBadges.appendChild(badge);
        }
    }
    
    // Add upgrade button if not on premium
    const upgradeButton = features.subscription_tier !== 'PREMIUM' ? `
        <button onclick="requestUpgrade()" class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
            </svg>
            Upgrade to Premium
        </button>
    ` : '';
    
    // Find or create features container
    let featuresContainer = document.getElementById('userFeaturesContainer');
    if (!featuresContainer) {
        featuresContainer = document.createElement('div');
        featuresContainer.id = 'userFeaturesContainer';
        featuresContainer.className = 'bg-white rounded-lg shadow-sm p-4 mb-6';
        document.querySelector('.max-w-3xl').insertBefore(featuresContainer, document.querySelector('.max-w-3xl').firstChild);
    }
    
    // Update features container
    featuresContainer.innerHTML = `
        <div class="text-center">
            <h3 class="text-lg font-medium text-gray-900 mb-2">Your Plan Features</h3>
            ${videoQualityInfo.outerHTML}
            ${slidesLimitInfo.outerHTML}
            ${durationInfo.outerHTML}
            ${featureBadges.outerHTML}
            ${upgradeButton}
        </div>
    `;
    
    // Update UI elements based on available features
    const saveScriptsBtn = document.getElementById('saveScriptsBtn');
    if (saveScriptsBtn) {
        if (!features.features.includes('custom_scripts')) {
            saveScriptsBtn.disabled = true;
            saveScriptsBtn.title = 'Upgrade to enable custom scripts';
            saveScriptsBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            saveScriptsBtn.disabled = false;
            saveScriptsBtn.title = 'Save script changes';
            saveScriptsBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }
}

function signOut() {
    google.accounts.id.disableAutoSelect();
    localStorage.removeItem('token');
    showAuthSection();
    window.location.reload();
}

function showMainContent() {
    console.log('Showing main content');
    document.getElementById('authSection').classList.add('hidden');
    document.getElementById('mainContent').classList.remove('hidden');
    document.getElementById('userMenu').classList.remove('hidden');
    document.getElementById('signInContainer').classList.add('hidden');
}

function showAuthSection() {
    console.log('Showing auth section');
    document.getElementById('authSection').classList.remove('hidden');
    document.getElementById('mainContent').classList.add('hidden');
    document.getElementById('userMenu').classList.add('hidden');
    document.getElementById('signInContainer').classList.remove('hidden');
}

function showMessage(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-4 rounded-lg shadow-lg text-white ${
        type === 'error' ? 'bg-red-500' : 'bg-indigo-600'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Add event listeners for file upload and processing
document.addEventListener('DOMContentLoaded', function() {
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) return;

    // Add file upload section to main content
    mainContent.innerHTML = `
        <div class="max-w-3xl mx-auto">
            <div class="bg-white rounded-lg shadow-sm p-6 mb-8">
                <div class="text-center mb-8">
                    <h2 class="text-3xl font-bold text-gray-900 mb-2">Upload Your Images</h2>
                    <p class="text-gray-500">Create engaging video presentations from your images</p>
                </div>
                
                <div id="dropZone" class="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-indigo-500 transition-colors cursor-pointer">
                    <input type="file" id="fileInput" class="hidden" multiple accept="image/*">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                    </svg>
                    <p class="mt-4 text-sm text-gray-500">
                        Drag and drop your images here, or click to select files
                    </p>
                    <p class="mt-1 text-xs text-gray-400">
                        Supports: PNG, JPG, JPEG
                    </p>
                </div>
                
                <div id="fileList" class="mt-6 space-y-2"></div>
                
                <div class="mt-6 text-center">
                    <button id="uploadBtn" disabled class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                        </svg>
                        Process Images
                    </button>
                </div>
            </div>
            
            <!-- Processing Status -->
            <div id="statusBox" class="hidden bg-white rounded-lg shadow-sm p-6 mb-8">
                <div class="text-center">
                    <svg class="animate-spin h-8 w-8 text-indigo-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">Processing</h3>
                    <div class="w-full bg-gray-200 rounded-full h-2.5">
                        <div class="bg-indigo-600 h-2.5 rounded-full" style="width: 0%" id="progressBar"></div>
                    </div>
                    <p class="mt-2 text-sm text-gray-500" id="statusText">Initializing...</p>
                </div>
            </div>
            
            <!-- Results Section -->
            <div id="resultBox" class="hidden space-y-8">
                <!-- Scripts Editor -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <div class="text-center mb-6">
                        <h3 class="text-lg font-medium text-gray-900">Customize Narration</h3>
                        <p class="text-sm text-gray-500">Edit the generated scripts for each slide</p>
                    </div>
                    <div id="scriptContent" class="space-y-4"></div>
                    <div class="mt-6 text-center">
                        <button id="saveScriptsBtn" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Save Changes
                        </button>
                    </div>
                </div>
                
                <!-- Video Creation -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <div class="text-center">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">Generate Video</h3>
                        
                        <!-- Video Creation Button Section -->
                        <div id="videoCreationSection">
                            <button id="createVideoBtn" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                                </svg>
                                Create Video
                            </button>
                        </div>
                        
                        <!-- Video Processing Status -->
                        <div id="videoProcessingStatus" class="hidden mt-6">
                            <div class="flex justify-center mb-4">
                                <svg class="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            </div>
                            <p class="text-sm text-gray-500">Creating your video presentation...</p>
                        </div>
                        
                        <!-- Video Download Section -->
                        <div id="videoDownloadSection" class="hidden mt-6 p-6 bg-gray-50 rounded-lg">
                            <div class="flex items-center justify-center mb-4">
                                <svg class="h-8 w-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                                </svg>
                            </div>
                            <h4 class="text-lg font-medium text-gray-900 mb-2">Video Ready!</h4>
                            <p class="text-sm text-gray-500 mb-4">Your presentation video has been generated successfully.</p>
                            
                            <!-- Video Preview -->
                            <div class="mb-4">
                                <video id="videoPreview" class="w-full rounded-lg shadow-sm" controls>
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                            
                            <a id="videoDownloadBtn" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                                </svg>
                                Download Video
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Initialize file upload functionality
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const uploadBtn = document.getElementById('uploadBtn');

    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-indigo-500', 'bg-indigo-50');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-indigo-500', 'bg-indigo-50');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-indigo-500', 'bg-indigo-50');
        handleFiles(e.dataTransfer.files);
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        handleFiles(fileInput.files);
    });

    function handleFiles(files) {
        selectedFiles = Array.from(files);
        
        // Sort files by name
        selectedFiles.sort((a, b) => a.name.localeCompare(b.name, undefined, {numeric: true}));
        
        // Update file list UI
        fileList.innerHTML = selectedFiles.map((file, index) => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center">
                    <span class="text-sm font-medium text-gray-900">${file.name}</span>
                    <span class="ml-2 text-sm text-gray-500">(${formatFileSize(file.size)})</span>
                </div>
                <button onclick="removeFile(${index})" class="text-red-500 hover:text-red-700">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `).join('');
        
        uploadBtn.disabled = selectedFiles.length === 0;
    }

    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        handleFiles(selectedFiles);
    };

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Upload button handler
    uploadBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            uploadBtn.disabled = true;
            document.getElementById('statusBox').classList.remove('hidden');
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const data = await response.json();
            processingId = data.processing_id;
            
            // Start polling for status
            pollStatus();
            
        } catch (error) {
            console.error('Upload error:', error);
            showMessage('Failed to upload files. Please try again.', 'error');
            uploadBtn.disabled = false;
            document.getElementById('statusBox').classList.add('hidden');
        }
    });

    // Status polling
    async function pollStatus() {
        try {
            const response = await fetch(`/status/${processingId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to get status');
            }

            const data = await response.json();
            updateProgress(data.progress, data.status);

            if (data.status === 'completed') {
                await loadScripts();
                document.getElementById('statusBox').classList.add('hidden');
                document.getElementById('resultBox').classList.remove('hidden');
            } else if (data.status === 'failed') {
                throw new Error(data.error || 'Processing failed');
            } else {
                setTimeout(pollStatus, 1000);
            }
        } catch (error) {
            console.error('Status polling error:', error);
            showMessage(error.message, 'error');
            document.getElementById('statusBox').classList.add('hidden');
        }
    }

    function updateProgress(progress, status) {
        const progressBar = document.getElementById('progressBar');
        const statusText = document.getElementById('statusText');
        
        progressBar.style.width = `${progress}%`;
        statusText.textContent = status;
    }

    // Load and display scripts
    async function loadScripts() {
        try {
            const response = await fetch(`/scripts/${processingId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load scripts');
            }

            const data = await response.json();
            const scriptContent = document.getElementById('scriptContent');
            
            scriptContent.innerHTML = data.scripts.map((script, index) => `
                <div class="p-4 bg-gray-50 rounded-lg">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Slide ${index + 1}</label>
                    <textarea
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                        rows="3"
                    >${script}</textarea>
                </div>
            `).join('');
        } catch (error) {
            console.error('Script loading error:', error);
            showMessage('Failed to load scripts', 'error');
        }
    }

    // Save scripts button handler
    document.getElementById('saveScriptsBtn').addEventListener('click', async () => {
        await saveScripts();
    });

    // Create video button handler
    document.getElementById('createVideoBtn').addEventListener('click', async () => {
        const button = document.getElementById('createVideoBtn');
        const videoProcessingStatus = document.getElementById('videoProcessingStatus');
        const videoCreationSection = document.getElementById('videoCreationSection');
        
        button.disabled = true;
        videoCreationSection.classList.add('hidden');
        videoProcessingStatus.classList.remove('hidden');
        
        try {
            const response = await fetch(`/video/${processingId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to create video');
            }

            if (!data.video_path) {
                throw new Error('No video path returned from server');
            }

            // Get the first file name from selectedFiles to use as video title
            const videoTitle = selectedFiles.length > 0 
                ? selectedFiles[0].name.replace(/\.[^/.]+$/, "") 
                : "presentation";
                
            // Update video preview and download section
            const videoPreview = document.getElementById('videoPreview');
            videoPreview.src = data.video_path;
            videoPreview.load(); // Reload the video element
            
            // Set up download button with custom filename
            const videoDownloadBtn = document.getElementById('videoDownloadBtn');
            videoDownloadBtn.href = data.video_path;
            videoDownloadBtn.download = `${videoTitle}_video.mp4`;
            
            // Show the download section
            document.getElementById('videoDownloadSection').classList.remove('hidden');
            showMessage('Video created successfully');
        } catch (error) {
            console.error('Video creation error:', error);
            showMessage(error.message || 'Failed to create video', 'error');
            videoCreationSection.classList.remove('hidden');
        } finally {
            button.disabled = false;
            videoProcessingStatus.classList.add('hidden');
        }
    });
});

// Save scripts button handler
async function saveScripts() {
    const button = document.getElementById('saveScriptsBtn');
    button.disabled = true;
    
    try {
        const textareas = document.querySelectorAll('#scriptContent textarea');
        const updatedScripts = Array.from(textareas).map(ta => ta.value);
        
        const response = await fetch(`/scripts/${processingId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(updatedScripts)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save scripts');
        }

        showMessage('Scripts saved successfully');
        
        // Re-enable the create video button after successful save
        document.getElementById('createVideoBtn').disabled = false;
    } catch (error) {
        console.error('Script saving error:', error);
        showMessage(error.message || 'Failed to save scripts', 'error');
    } finally {
        // Only disable the button if the user doesn't have custom_scripts feature
        const features = JSON.parse(localStorage.getItem('userFeatures'));
        if (features && features.features.includes('custom_scripts')) {
            button.disabled = false;
        }
    }
}

// Add the upgrade request function
async function requestUpgrade() {
    try {
        // Create order
        const orderResponse = await fetch('/api/payments/create-order', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            }
        });

        if (!orderResponse.ok) {
            const error = await orderResponse.json();
            throw new Error(error.error?.description || 'Failed to create order');
        }

        const orderData = await orderResponse.json();
        
        // Create mock payment modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-10 overflow-y-auto';
        modal.innerHTML = `
            <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                <div class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                    <div class="absolute right-0 top-0 pr-4 pt-4">
                        <button type="button" onclick="closeMockPaymentModal()" class="rounded-md bg-white text-gray-400 hover:text-gray-500">
                            <span class="sr-only">Close</span>
                            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <div class="sm:flex sm:items-start">
                        <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                            <h3 class="text-xl font-semibold leading-6 text-gray-900 mb-4">Complete Payment</h3>
                            <div class="mt-2">
                                <div class="text-sm text-gray-500 mb-4">
                                    <p>Amount: ₹${(orderData.amount / 100).toFixed(2)}</p>
                                    <p>Order ID: ${orderData.id}</p>
                                </div>
                                <button onclick="simulateSuccessfulPayment()" 
                                        class="w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
                                    Pay Now
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity';
        
        // Add to document
        document.body.appendChild(backdrop);
        document.body.appendChild(modal);
        
        // Store order data for simulation
        window.currentOrderData = orderData;
        
    } catch (error) {
        console.error('Payment initiation error:', error);
        showMessage(error.message || 'Failed to initiate payment', 'error');
    }
}

function closeMockPaymentModal() {
    const modal = document.querySelector('.fixed.z-10');
    const backdrop = document.querySelector('.fixed.bg-gray-500');
    if (modal) modal.remove();
    if (backdrop) backdrop.remove();
    delete window.currentOrderData;
}

async function simulateSuccessfulPayment() {
    try {
        const orderData = window.currentOrderData;
        if (!orderData) {
            throw new Error('No active payment session');
        }

        // Simulate payment success
        const mockResponse = {
            razorpay_order_id: orderData.id,
            razorpay_payment_id: 'pay_' + Math.random().toString(36).substr(2, 9),
            razorpay_signature: 'mock_signature_' + Date.now()
        };

        // Call the payment handler
        const verifyResponse = await fetch('/api/payments/verify-payment', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                orderId: mockResponse.razorpay_order_id,
                paymentId: mockResponse.razorpay_payment_id,
                signature: mockResponse.razorpay_signature
            })
        });

        if (!verifyResponse.ok) {
            const error = await verifyResponse.json();
            throw new Error(error.error?.description || 'Payment verification failed');
        }

        const result = await verifyResponse.json();
        showMessage(result.message, 'info');
        
        // Close payment modal
        closeMockPaymentModal();
        
        // Reload user features to update UI
        await loadUserProfile();
        
    } catch (error) {
        console.error('Payment simulation error:', error);
        showMessage(error.message || 'Failed to process payment', 'error');
    }
}