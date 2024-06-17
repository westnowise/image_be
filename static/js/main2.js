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

// 로딩 화면을 보이게 하는 함수
function showLoading() {
    var loadingScreen = document.getElementById('loadingScreen');
    loadingScreen.style.display = 'block'; // 화면에 보이게 함

    // running 작업이 끝날 때까지 로딩 화면을 보이게 유지
}

// 버튼 클릭 이벤트 핸들러
var button = document.querySelector('.running');
button.addEventListener('click', function(event) {
    event.preventDefault(); // 기본 동작 방지 (페이지 새로고침 등)

    showLoading(); // 로딩 화면을 보이게 함

    // 여기서 실제로 running 작업을 수행
    // 예시로 setTimeout을 사용하여 5초 후에 작업이 끝났다고 가정
    setTimeout(function() {
        // 실제 running 작업이 끝난 후에 로딩 화면을 숨김
        var loadingScreen = document.getElementById('loadingScreen');
        loadingScreen.style.display = 'none';
    }, 5000); // 예시로 5초(5000밀리초) 후에 실행
});