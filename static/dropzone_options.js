let urlParams = new URLSearchParams(window.location.search);

Dropzone.autoDiscover = false;

let myDropzone = new Dropzone("div#mwdrop", {
	url: "http://127.0.0.1:5000/util/s3/upload/" + urlParams.get('email'),
	dictDefaultMessage: "Choose/drag files here",
	acceptedFiles: "image/*,application/pdf",
	maxFilesize: 6,
	resizeWidth: 1200
});