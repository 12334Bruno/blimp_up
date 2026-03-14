// 
var slideIndex = 1;
var map = null
var marker = null

// Refresh a page when using travel arrows
window.addEventListener( "pageshow", function ( event ) {
    var historyTraversal = event.persisted || 
                           ( typeof window.performance != "undefined" && 
                                window.performance.navigation.type === 2 );
    if ( historyTraversal ) {
      // Handle page restore.
      window.location.reload();
    }
    
});


function handleForm(event) { event.preventDefault(); } 

window.addEventListener("DOMContentLoaded", () => {

    // Render map
    try {
        if (data.map == true) {

            mapboxgl.accessToken = 'pk.eyJ1IjoiYnJ1bmlkZW9zIiwiYSI6ImNsMDl0c3gxbTAzdWMzam56bzU5YWlvNGEifQ.lKHGPlhKt5qHYs3J0SZqFw';

            // If the map is on the register page
            if (data.register_blimp_page) { 
                
                map = new mapboxgl.Map({
                    container: 'map',
                    style: 'mapbox://styles/mapbox/dark-v10',
                    zoom: 1,
                    center: [0, 30]
                })

                    addUserMarkers(map);
                    
            } else if (data.blimp_page) { // Else if the map is on the blimp page
                map = new mapboxgl.Map({
                    container: 'map',
                    style: 'mapbox://styles/mapbox/dark-v10',
                    zoom: 3,
                    center: [data.longitude, data.latitude]
                })

                showDivs(slideIndex); // Initiate image slide show
                marker = new mapboxgl.Marker({ // Place blimp location marker
                color: "#e40613",
                }).setLngLat([data.longitude, data.latitude])
                .addTo(map);

                if (data.editing) {
                    addUserMarkers(map);
                }
                
            } else if (data.blimp_locations) {

                document.getElementById("map").style.width = "90%";
                document.getElementById("map").style.height = "600px";
                map = new mapboxgl.Map({
                    container: 'map',
                    style: 'mapbox://styles/mapbox/dark-v10',
                    zoom: 1
                })

                // Go over every blimp location, create a marker and popup for each blimp
                console.log(Object.keys(data.blimp_locations).length)
                for (let i = 0; i < Object.keys(data.blimp_locations).length; i++) {

                    element = data.blimp_locations[Object.keys(data.blimp_locations)[i]]

                    // create the popup
                    const popup = new mapboxgl.Popup({ offset: 25 })
                    .setHTML(
                        '<a style="text-decoration: none; color: black; width: auto" href="/blimp/' + element.blimp_id + '"><h4 style="text-align: center; margin-top: 10px">' + element.blimpname + '</h4><img class="blimp-post-img" src="' + element.image + '" style="width:100%;height: 10rem; object-fit: cover; padding-bottom: 0px" alt="img"></img>'
                    );

                    console.log(element)
                    marker = new mapboxgl.Marker({ // Place blimp location marker
                    color: "#e40613",
                    }).setLngLat([element.longitude, element.latitude])
                    .addTo(map)
                    .setPopup(popup) // sets a popup on this marker
                    .addTo(map);
                    
                }

            }
        }
    } catch {} // If no data is passed in

    
    // Reload on the same part of the page by gani on https://stackoverflow.com/questions/26112503/scroll-to-same-position-on-reload-and-load
    localStorage.setItem("scrollTop", document.body.scrollTop);
    window.onload = function() {  
        var scroll = parseInt(localStorage.getItem("scrollTop"));
        //parseInt(localStorage.scrollTop);   
        if (!isNaN(scroll))
        document.body.scrollTop = scroll;
        
    }

    var selectObj = {
        oldest: 2,
        newest: 1,
        "0": 3,
        "1": 4,
        "2": 5,
        "3": 6,
        "4": 7,
        "5": 8
    }

    // Check pagination, add a filter parameter if one exists
    const urlParams = new URLSearchParams(window.location.href.split('?')[1]);
    if (urlParams.has("filter")) {
        document.querySelectorAll(".add_filter").forEach(element => {
            element.href += "&filter=" + urlParams.get("filter")
            if (element.href.indexOf("#") == -1) {
                element.href += "#reviews-title"
            }
        })
        if (document.querySelector("#blimp-filter-select") != null) {
            document.querySelector("#blimp-filter-select").selectedIndex = selectObj[urlParams.get("filter").split("#")[0]];
        }
    }

    // Error checking for forms
    document.querySelectorAll(".requests-form").forEach(form => {
        form.addEventListener('submit', handleForm);
    })
    document.querySelectorAll(".errorlist").forEach((element) => { 
        // Change the border from red to noraml and remove the error message when the user types something
        element.parentNode.childNodes[1].style.border = "1px solid red"
        if (element.parentNode.childNodes[1].nodeName == "INPUT") {
            element.parentNode.childNodes[1].addEventListener("keyup", function() {
                if (this.parentNode.childNodes[3] != undefined) {
                this.style.border = "1px solid #e0e4e7";
                this.parentNode.childNodes[3].remove()
            }
            }) // Same thing but for a file type input
            if (element.parentNode.childNodes[1].type == "file") {
                element.parentNode.childNodes[1].addEventListener("change", function() {
                    if (this.parentNode.childNodes[3] != undefined) {
                        this.style.border = "1px solid #e0e4e7";
                        this.parentNode.childNodes[3].remove()
                    }
                })
            }
        } else { // Same thing but for a select type input
            element.parentNode.childNodes[1].addEventListener("change", function() {
                if (this.parentNode.childNodes[3] != undefined) {
                    this.style.border = "1px solid #e0e4e7";
                    this.parentNode.childNodes[3].remove()
                }
            })
        }
    })

    
})

function addUserMarkers(map) {
    // Create marker where the user clicks
    map.on('style.load', function() {
        map.on('click', function(e) {
            if (marker != null) { // Clear last marker
                marker.remove();
            }

            try {
                document.getElementById("map").style.border = "0px solid black";
                document.getElementById("map-error").remove();
            }
            catch {}
            // Set input form values to placed markers values
            var coordinates = e.lngLat;
            document.querySelector("#map-coords-lng").value = coordinates.lng;
            document.querySelector("#map-coords-lat").value = coordinates.lat;
            
            // Set marker options.
            marker = new mapboxgl.Marker({
            color: "#e40613",
            }).setLngLat([coordinates.lng, coordinates.lat])
            .addTo(map);
        });
    });
}

// Blimp page slide show with the picture and map
function plusDivs(n, elem, button) {
    if (slideIndex !== n) {
        elem.classList.add("selected-button")
        button.classList.remove("selected-button")
        showDivs(slideIndex = n);
    }
}

function showDivs(n) {
    var x = document.getElementsByClassName("mySlides");
    if (n > x.length) {slideIndex = 1}
    if (n < 1) {slideIndex = x.length} ;
    for (let i = 0; i < x.length; i++) {
        x[i].style.display = "none";
    }
    try {
        x[slideIndex-1].style.display = "block";
    } catch {}
    
    map.resize(); // Resize map
}


// Function to filter all reviews (eg. oldest reviews, reviews with only 1 star...)
function filter_reviews(event) {
    event.preventDefault(); // Prevent the page from refreshing
    filter = event.target.elements["filter_option"].value;
    window.location.assign(window.location.href.split("?")[0] + "?filter=" + filter + "#reviews-title");

}

// Function for manual page navigation, the user can type the number of a page they want to go to
function reviews_page(event) {
    event.preventDefault(); // Prevent the page from refreshing
    page = event.target.childNodes[0].value; // Get page the user wants to go to
    const urlParams = new URLSearchParams(window.location.href.split('?')[1]);
    parameters = "?page=" + page + "&"
    if (urlParams.has("filter")) {
        parameters += "filter=" + urlParams.get("filter")
    }
    window.location.assign(window.location.href.split("?")[0] + parameters);
}

// Function for accepting/rejecting a passenger to a flight
function trip_requests(event) {
    form = event.target.parentElement

    removeElement(form.parentElement.parentElement)

    // Send data
    fetch('http://127.0.0.1:8000/trip_requests', {
        method: 'POST',
        credentials: 'same-origin',
        headers:{
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest', //Necessary to work with request.is_ajax()
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({
            "id": form.elements["id"].value,
            "username": form.elements["username"].value,
            "choice": form.elements["choice"].value,
        })
    })

}

// Function for signing up for a flight
function sign_up() {

    // Switch the button name when clicked (form "Request flight" to "Remove request" and vice versa)
    var message = "Request flight"
    var sign_up = false
    trip_btn = document.getElementById("blimp-signupbtn")
    if (trip_btn.innerHTML.trim() == message) {
        message = "Remove request"
        sign_up = true
    } else if (data.accepted) {
        element = document.getElementById("blimp-capacity").childNodes[1]
        element.innerHTML = `<span class='material-icons'>groups</span> ${data.filled_capacity - 1}/${data.capacity}`
    }

    // Send data
    fetch('http://127.0.0.1:8000/sign_up', {
        method: 'POST',
        credentials: 'same-origin',
        headers:{
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest', //Necessary to work with request.is_ajax()
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({
            "id": data.id,
            "sign_up": sign_up
        })
    })

    trip_btn.innerHTML = message
}

// Function for an owner of a trip to start/end a trip
function trip_action() {
    // Send data
    fetch(`http://127.0.0.1:8000/blimp/${data.id}`, {
        method: 'POST',
        credentials: 'same-origin',
        headers:{
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest', // Necessary to work with request.is_ajax()
            'X-CSRFToken': csrftoken,
        }
    })

    // Switch button name (from "Start trip" to "End trip" and vice versa)
    var message = "Start trip"
    trip_btn = document.getElementById("blimp-tripbtn")
    if (trip_btn.innerHTML.trim() == message) {
        message = "End trip"
        document.querySelector("#blimp-status").innerHTML = "<b>Status:</b><div class='blimp-notavailable blimppill' style='position: relative;'>Not Available</div>"
    } else {
        document.querySelector("#blimp-status").innerHTML = "<b>Status:</b><div class='blimp-available blimppill' style='position: relative; background-color: rgb(55, 55, 255);'>Available</div>"
        element = document.getElementById("blimp-capacity").childNodes[1]
        element.innerHTML = `<span class='material-icons'>groups</span> 0/${data.capacity}`
    }
    trip_btn.innerHTML = message
}

// Remove element (using an animation to make it smooth)
function removeElement(elem) {
    if (elem.nodeType != 1) {
        return
    }
    elem.classList.add("disappear")
    elem.childNodes.forEach((element) => {
        removeElement(element)
    })
    setTimeout(() => {
        elem.remove()
    }, 1500)
}

// Get csrf_token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

