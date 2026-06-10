import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/medicines'
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { publicOnly: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { publicOnly: true }
  },
  {
    path: '/invite/:token',
    name: 'accept-invite',
    component: () => import('../views/AcceptInviteView.vue'),
    meta: { public: true }
  },
  {
    path: '/medicines',
    name: 'medicines',
    component: () => import('../views/MedicinesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/shopping',
    name: 'shopping',
    component: () => import('../views/ShoppingView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/changelog',
    name: 'changelog',
    component: () => import('../views/ChangeLogView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/invitations',
    name: 'invitations',
    component: () => import('../views/InvitationsView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/medicines'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.bootstrap()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'medicines' }
  }

  if (to.meta.publicOnly && auth.isAuthenticated) {
    return { name: 'medicines' }
  }

  return true
})

export default router
