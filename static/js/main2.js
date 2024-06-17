const imageInput = document.getElementById('imageInput');
const previewImage = document.getElementById('previewImage');

imageInput.addEventListener('change', function() {
    const file = this.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            previewImage.src = event.target.result;
            previewImage.style.width = '512px';
            previewImage.style.height = '512px';
        };
        reader.readAsDataURL(file);
        console.log('Selected image file path:', URL.createObjectURL(file));
    }
});

function validateForm() {
    const numImagesPerPrompt = document.getElementById("num_images_per_prompt");
    const maxNumImagesPerPrompt = 4;

    if (parseInt(numImagesPerPrompt.value) > maxNumImagesPerPrompt) {
        alert(`Number of Images per Prompt cannot be more than ${maxNumImagesPerPrompt}.`);
        numImagesPerPrompt.focus();
        return false;
    }
    return true;
}

let currentIndex = 0;

function showSlide(index) {
    const slides = document.querySelectorAll('.slide');
    const totalSlides = slides.length;
    if (index >= totalSlides) {
        currentIndex = 0;
    } else if (index < 0) {
        currentIndex = totalSlides - 1;
    } else {
        currentIndex = index;
    }
    slides.forEach((slide, i) => {
        slide.style.display = (i === currentIndex) ? 'block' : 'none';
    });
}

function nextSlide() {
    showSlide(currentIndex + 1);
}

function prevSlide() {
    showSlide(currentIndex - 1);
}

document.querySelectorAll('.item').forEach((item, index) => {
    item.addEventListener('click', function() {
        showSlide(parseInt(this.getAttribute('data-index')));
    });
});

showSlide(currentIndex); // Initialize the first slide

document.addEventListener('DOMContentLoaded', () => {
    const slider = document.getElementById('slider');
    const sliderValue = document.getElementById('slider-value');

    slider.addEventListener('input', () => {
        sliderValue.textContent = parseFloat(slider.value).toFixed(2);
    });
});

function submitForm() {
    document.getElementById('controlForm').submit();
}

function saveCurrentImage() {
    let slides = document.getElementsByClassName("slide");
    let currentSlide = slides[currentIndex];
    let imgElement = currentSlide.getElementsByTagName("img")[0];
    let imgSrc = imgElement.src;

    // Create a temporary anchor element to download the image
    let a = document.createElement("a");
    a.href = imgSrc;
    a.download = `generated_image_${currentIndex + 1}.png`; // Set the filename
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// Event listener for save button
document.querySelector('.save').addEventListener('click', saveCurrentImage);

document.querySelector('.running').addEventListener('click', function() {
    const loading = document.getElementById('loading');
    loading.classList.remove('hidden');

    
    setTimeout(function() {
        loading.classList.add('hidden');
       
    }, 5000); 
});

document.getElementById('myForm').addEventListener('submit', function(event) {
    const requiredFields = [
        'prompt',
        'negative_prompt',
        'num_inference_steps',
        'num_images_per_prompt',
        'guidance_scale',
        'seed',
        'batch_size',
        'batch_count',
        'slider',
        'imageInput'
    ];

    let isValid = true;

    requiredFields.forEach(function(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field.value) {
            isValid = false;
            field.style.borderColor = 'red'; // 입력되지 않은 필드에 빨간색 테두리를 추가합니다.
        } else {
            field.style.borderColor = ''; // 입력된 필드의 테두리를 초기화합니다.
        }
    });

    if (!isValid) {
        event.preventDefault(); // 폼 제출을 막습니다.
        alert('모든 필수 입력 필드를 입력해 주세요.');
    }
});