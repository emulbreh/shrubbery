$(document).ready(function(){
	$('a[href^=http://docs.djangoproject.com/].reference.external').addClass('django-docs');
	$('a[href^=http://].reference.external').addClass('foreign');
});