// ======================================
// INTERVIEW AI - PREMIUM INTERACTIONS
// ======================================

// Mouse Glow Effect
const glow = document.querySelector(".cursor-glow");

document.addEventListener("mousemove", (e) => {
    if (!glow) return;

    glow.style.left = e.clientX + "px";
    glow.style.top = e.clientY + "px";
});

// ======================================
// GSAP SETUP
// ======================================

gsap.registerPlugin(ScrollTrigger);

// ======================================
// HERO ANIMATIONS
// ======================================

gsap.from(".navbar", {
    y: -80,
    opacity: 0,
    duration: 1,
    ease: "power3.out"
});

gsap.from(".hero-badge", {
    y: 30,
    opacity: 0,
    duration: 0.8,
    delay: 0.2
});

gsap.from(".hero h1", {
    y: 80,
    opacity: 0,
    duration: 1,
    delay: 0.3,
    ease: "power3.out"
});

gsap.from(".hero p", {
    y: 40,
    opacity: 0,
    duration: 1,
    delay: 0.5
});

gsap.from(".hero-buttons", {
    y: 40,
    opacity: 0,
    duration: 1,
    delay: 0.7
});

gsap.from(".hero-stats .stat", {
    y: 30,
    opacity: 0,
    duration: 0.8,
    stagger: 0.15,
    delay: 0.9
});

gsap.from(".interview-card", {
    x: 100,
    opacity: 0,
    duration: 1.2,
    delay: 0.6,
    ease: "power3.out"
});

// ======================================
// FLOATING CARD EFFECT
// ======================================

const interviewCard = document.querySelector(".interview-card");

if (interviewCard) {
    document.addEventListener("mousemove", (e) => {

        const x = (window.innerWidth / 2 - e.clientX) / 40;
        const y = (window.innerHeight / 2 - e.clientY) / 40;

        interviewCard.style.transform =
            `rotateY(${-x}deg) rotateX(${y}deg)`;
    });

    document.addEventListener("mouseleave", () => {
        interviewCard.style.transform =
            "rotateY(0deg) rotateX(0deg)";
    });
}

// ======================================
// FEATURE CARD REVEAL
// ======================================

gsap.utils.toArray(".feature-card").forEach((card, i) => {

    gsap.from(card, {
        scrollTrigger: {
            trigger: card,
            start: "top 85%"
        },
        y: 80,
        opacity: 0,
        duration: 0.8,
        delay: i * 0.05,
        ease: "power3.out"
    });

});

// ======================================
// STEP ANIMATION
// ======================================

gsap.utils.toArray(".step").forEach((step) => {

    gsap.from(step, {
        scrollTrigger: {
            trigger: step,
            start: "top 85%"
        },
        y: 60,
        opacity: 0,
        duration: 1
    });

});

// ======================================
// PARALLAX EFFECT
// ======================================

window.addEventListener("scroll", () => {

    const scroll = window.pageYOffset;

    document.querySelectorAll(".feature-card").forEach((card, index) => {

        const speed = (index % 3 + 1) * 0.03;

        card.style.transform =
            `translateY(${scroll * speed * 0.05}px)`;
    });

});

// ======================================
// COUNTER ANIMATION
// ======================================

function animateCounter(element, target) {

    let current = 0;

    const increment = target / 80;

    const timer = setInterval(() => {

        current += increment;

        if (current >= target) {
            current = target;
            clearInterval(timer);
        }

        if (target >= 1000000) {
            element.innerText =
                (current / 1000000).toFixed(1) + "M+";
        }
        else if (target >= 1000) {
            element.innerText =
                Math.floor(current / 1000) + "K+";
        }
        else {
            element.innerText =
                Math.floor(current) + "%";
        }

    }, 20);
}

const stats = document.querySelectorAll(".stat");

if (stats.length >= 3) {

    ScrollTrigger.create({
        trigger: ".hero-stats",
        start: "top 85%",
        once: true,

        onEnter: () => {

            stats[0].innerHTML =
                "<span class='counter'>0</span>";

            stats[1].innerHTML =
                "<span class='counter'>0</span>";

            stats[2].innerHTML =
                "<span class='counter'>0</span>";

            animateCounter(
                stats[0].querySelector(".counter"),
                94
            );

            animateCounter(
                stats[1].querySelector(".counter"),
                50000
            );

            animateCounter(
                stats[2].querySelector(".counter"),
                10000000
            );
        }
    });

}

// ======================================
// NAVBAR SCROLL EFFECT
// ======================================

const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {

    if (!navbar) return;

    if (window.scrollY > 50) {

        navbar.style.background =
            "rgba(5,5,5,0.95)";

        navbar.style.boxShadow =
            "0 10px 40px rgba(0,0,0,.35)";
    }
    else {

        navbar.style.background =
            "rgba(5,5,5,.7)";

        navbar.style.boxShadow = "none";
    }
});

// ======================================
// BUTTON RIPPLE EFFECT
// ======================================

document.querySelectorAll(
    ".hero-primary,.primary-btn"
).forEach((button) => {

    button.addEventListener("click", function (e) {

        const circle =
            document.createElement("span");

        const diameter =
            Math.max(
                this.clientWidth,
                this.clientHeight
            );

        circle.style.width =
            circle.style.height =
            diameter + "px";

        circle.style.left =
            e.offsetX - diameter / 2 + "px";

        circle.style.top =
            e.offsetY - diameter / 2 + "px";

        circle.classList.add("ripple");

        const ripple =
            this.getElementsByClassName("ripple")[0];

        if (ripple) ripple.remove();

        this.appendChild(circle);
    });

});

// ======================================
// SMOOTH SECTION REVEAL
// ======================================

gsap.utils.toArray("section").forEach((section) => {

    gsap.from(section, {
        scrollTrigger: {
            trigger: section,
            start: "top 92%"
        },
        opacity: 0,
        duration: 1
    });

});

// ======================================
// HERO TEXT FLOATING
// ======================================

gsap.to(".hero h1", {
    y: -10,
    duration: 3,
    repeat: -1,
    yoyo: true,
    ease: "sine.inOut"
});

// ======================================
// LIVE STATUS PULSE
// ======================================

gsap.to(".live-dot", {
    opacity: 0.4,
    duration: 0.8,
    repeat: -1,
    yoyo: true
});

// ======================================
// PAGE LOADER
// ======================================

window.addEventListener("load", () => {

    document.body.classList.add("loaded");

    gsap.from("body", {
        opacity: 0,
        duration: 0.6
    });

});

// ======================================
// FEATURE CARD TILT
// ======================================

document.querySelectorAll(".feature-card")
.forEach((card) => {

    card.addEventListener("mousemove", (e) => {

        const rect =
            card.getBoundingClientRect();

        const x =
            e.clientX - rect.left;

        const y =
            e.clientY - rect.top;

        const rotateY =
            ((x / rect.width) - 0.5) * 12;

        const rotateX =
            ((y / rect.height) - 0.5) * -12;

        card.style.transform =
            `perspective(1000px)
             rotateX(${rotateX}deg)
             rotateY(${rotateY}deg)
             translateY(-8px)`;
    });

    card.addEventListener("mouseleave", () => {

        card.style.transform =
            "perspective(1000px) rotateX(0) rotateY(0)";
    });

});

console.log(
    "🚀 InterviewAI Premium UI Loaded"
);
