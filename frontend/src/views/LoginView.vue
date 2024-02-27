<template>

    <body class="bg-gray-100 flex items-center justify-center h-screen">
        <div class="flex flex-col items-center">
            <form @submit.prevent="login" class="flex flex-col">
                <input type="email" v-model="email" placeholder="EMAIL"
                    class="bg-transparent border-none py-2 focus:outline-none" required>
                <input type="password" v-model="password" placeholder="PASSWORD"
                    class="bg-transparent border-none py-2 focus:outline-none" required>
                <br>
                <button type="submit" class="button">ENTER</button>
            </form>
        </div>
    </body>
</template>



<script>
import axios from 'axios';

export default {
    data() {
        return {
            email: '',
            password: '',
        };
    },
    methods: {
        async login() {
            try {
                // Create FormData object
                let formData = new FormData();
                formData.append('username', this.email);
                formData.append('password', this.password);
                const response = await axios.post('http://localhost:8000/auth/cookie_token', formData, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    withCredentials: true,
                }); 
                console.log(response);
                if (response.status === 200) {
                    this.$router.push('/hello');
                }
            } catch (error) {
                alert('Login failed!');
            }
        },
    },
};
</script>
  
<style scoped>
body {
    color: #2C2C2C;
}

.hidden {
    display: none;
}

.button {
    color: #000;
    font-weight: bold;
    background-color: #c3c3c3;
    border: none;
    border-radius: 0.5rem;
    padding: 0.05rem 0.2rem;
    transition: background-color 0.3s, transform 0.3s;
    width: 4rem;
}

.button:hover {
    transform: scale(1.03);
}

input {
    color: #2C2C2C;
}

.error-message {
    color: red;
    margin-top: 10px;
}
</style>
  