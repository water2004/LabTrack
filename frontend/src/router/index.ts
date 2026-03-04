import { createRouter, createWebHistory } from 'vue-router';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import AdminLogin from '../views/AdminLogin.vue';
import AdminDashboard from '../views/AdminDashboard.vue';

const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  { path: '/admin-login', component: AdminLogin },
  { path: '/admin', component: AdminDashboard },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from) => {
  const token = localStorage.getItem('token');
  const isAdminToken = localStorage.getItem('isAdmin') === 'true';

  if (to.path === '/admin' && !isAdminToken) {
    return '/admin-login';
  } else if (to.path !== '/login' && to.path !== '/admin-login' && !token && !isAdminToken) {
    return '/login';
  }
  return true;
});


export default router;
