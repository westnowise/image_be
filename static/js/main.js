document.getElementById('runningBtn').addEventListener('click', function() {
    var inputPrompt = document.getElementById('inputPrompt').value;
    var excludePrompt = document.getElementById('excludePrompt').value;
    var numInferenceSteps = document.getElementById('numInferenceSteps').value;
    var numImagesPerPrompt = document.getElementById('numImagesPerPrompt').value;
    var guidanceScale = document.getElementById('guidanceScale').value;
    var seed = document.getElementById('seed').value;
    var batchSize = document.getElementById('batchSize').value;
    var batchCount = document.getElementById('batchCount').value;

    // AJAX를 사용하여 서버로 값 전송
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/generate_image', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            // 이미지를 표시
            var imgResult = document.createElement('img');
            imgResult.src = URL.createObjectURL(xhr.response);
            document.querySelector('.result').appendChild(imgResult);
        }
    };
    xhr.responseType = 'blob';
    xhr.send('inputPrompt=' + inputPrompt + '&excludePrompt=' + excludePrompt + '&numInferenceSteps=' + numInferenceSteps + '&numImagesPerPrompt=' + numImagesPerPrompt + '&guidanceScale=' + guidanceScale + '&seed=' + seed + '&batchSize=' + batchSize + '&batchCount=' + batchCount);
});


document.querySelector('.save').addEventListener('click', function() {
    var resultImage = document.querySelector('.result img');
    var imageSrc = resultImage.src;
    var a = document.createElement('a');
    a.href = imageSrc;
    a.download = 'generated_image.png'; // 다운로드될 파일 이름
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
});
