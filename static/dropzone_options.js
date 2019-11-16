let urlParams = new URLSearchParams(window.location.search);

Dropzone.autoDiscover = false;

let myDropzone = new Dropzone("div#mwdrop", {
	url: "/s3/upload/" + urlParams.get('user'),
	dictDefaultMessage: "Choose/drag files here",
	acceptedFiles: "image/*,application/pdf",
	maxFilesize: 6,
	resizeWidth: 1200
});