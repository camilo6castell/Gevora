function validarFormulario(event){
    let user = document.getElementById("user")
    let pass = document.getElementById("pass")
    let pryv = document.getElementById("privacy")

    let formato_email = /^\w+([\.-]?\w+)@\w+([\.-]?\w+)(\.\w{2,3})+$/;
    if (!user.value.match(formato_email)) {
        event.preventDefault();
        alert("Debes ingresar un email electronico valido!");
        user.focus();
        return false;
    }    
    let checkpass = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$/;
    if (!checkpass.test(pass.value)){
        event.preventDefault();
        alert("La contraseña debe contener al menos una minúscula, una mayúscula, un número, un caracter especial y 8 caracteres");
        pass.focus();
        return false;
    }

    let pryvV = pryv.checked;    
    if (pryvV == false){
        alert("Debes aceptar los términos y condiciones")
        event.preventDefault();
        pryv.focus();
        return false
    }
}

function mostrarPassword(){    
    obj.type = "text";
  }
function ocultarPassword(){
    obj.type="password"
}

/* Validación form */

let sign_up_form = document.getElementById("sign_up_form");

sign_up_form.addEventListener("submit", validarFormulario);

/* Mostras/ocultar password */

let imagen = document.querySelector("#showpass");
let obj = document.getElementById("pass");

imagen.addEventListener("mouseover", mostrarPassword);
imagen.addEventListener("mouseout", ocultarPassword);
