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

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token');
  const isAdminToken = localStorage.getItem('isAdmin');

  if (to.path === '/admin' && !isAdminToken) {
    next('/admin-login');
  } else if (to.path !== '/login' && to.path !== '/admin-login' && !token && !isAdminToken) {
    next('/login');
  } else {
    next();
  }
});

export default router;
