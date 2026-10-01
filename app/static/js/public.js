const professional = document.querySelector("#professional_id");
const service = document.querySelector("#service_id");
const dateInput = document.querySelector("#date");
const timeSelect = document.querySelector("#start_time");
const form = document.querySelector("#booking-form");
const message = document.querySelector("#booking-message");

function updateTimes() {
    const professionalId = professional.value;
    const serviceId = service.value;
    const date = dateInput.value;

    timeSelect.innerHTML = '<option value="">Carregando...</option>';
    timeSelect.disabled = true;

    if (!professionalId || !serviceId || !date) {
        timeSelect.innerHTML = '<option value="">Escolha profissional, serviço e data</option>';
        return;
    }

    fetch(`/api/availability?professional_id=${professionalId}&service_id=${serviceId}&date=${date}`)
        .then(response => response.json())
        .then(data => {
            timeSelect.innerHTML = "";

            if (!data.available_times || data.available_times.length === 0) {
                timeSelect.innerHTML = '<option value="">Nenhum horário disponível</option>';
                return;
            }

            timeSelect.disabled = false;

            data.available_times.forEach(time => {
                const option = document.createElement("option");
                option.value = time;
                option.textContent = time;
                timeSelect.appendChild(option);
            });
        })
        .catch(() => {
            timeSelect.innerHTML = '<option value="">Erro ao carregar horários</option>';
        });
}

[professional, service, dateInput].forEach(element => {
    element.addEventListener("change", updateTimes);
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    message.textContent = "Enviando...";

    const payload = {
        professional_id: professional.value,
        service_id: service.value,
        date: dateInput.value,
        start_time: timeSelect.value,
        client_name: document.querySelector("#client_name").value,
        client_phone: document.querySelector("#client_phone").value
    };

    const response = await fetch("/api/appointments", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });

    const data = await response.json();
    message.textContent = data.message || data.error;

    if (response.ok) {
        form.reset();
        timeSelect.innerHTML = '<option value="">Escolha a data primeiro</option>';
        timeSelect.disabled = true;
    }
});
