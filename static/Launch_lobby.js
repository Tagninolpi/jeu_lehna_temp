
//---- Access to data form ----

const form = document.getElementById('param'); //defini le formulaire d'id=param en JavaScript (déjà pst ds HTML)

form.addEventListener('submit', (event) => { //se declenche si sousmission formulaire
  event.preventDefault(); //prevent usual form of being sent

  const formData = new FormData(form);


  //conversion en objet :
  const data = Object.fromEntries(formData.entries());
  console.log(data)
});



