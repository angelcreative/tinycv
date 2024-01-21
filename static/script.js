'use strict';

// Assuming this script is meant to run in a browser environment
document.getElementById('uploadButton').addEventListener('click', function () {
    document.getElementById('file').click();
});

document.getElementById('file').addEventListener('change', function () {
    // You can add more functionality here to update the button text
    // or to show the selected file name
});
