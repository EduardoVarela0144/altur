import { useState, ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Box,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useMediaQuery,
  useTheme,
  Theme,
} from '@mui/material'
import {
  PhoneCallback,
  Analytics,
  Menu as MenuIcon,
  Logout,
} from '@mui/icons-material'
import { useAuth } from '../hooks/useAuth'

interface LayoutProps {
  children: ReactNode
}

interface MenuItem {
  text: string
  path: string
  icon: typeof PhoneCallback
}

const Layout = ({ children }: LayoutProps) => {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const theme: Theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const { logout, user } = useAuth()

  const menuItems: MenuItem[] = [
    { text: 'Calls', path: '/', icon: PhoneCallback },
    { text: 'Analytics', path: '/analytics', icon: Analytics },
  ]

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen)
  }

  const handleNavigation = (path: string) => {
    navigate(path)
    if (isMobile) {
      setDrawerOpen(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ bgcolor: '#1976D2' }}>
        <Toolbar>
          {isMobile && (
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, fontWeight: 600 }}
          >
            Altur
          </Typography>
          {user && (
            <Typography variant="body2" sx={{ mr: 2 }}>
              {user.username}
            </Typography>
          )}
          <Button color="inherit" startIcon={<Logout />} onClick={async () => {
            await logout()
            // Small delay to ensure state is cleared
            setTimeout(() => {
              navigate('/login', { replace: true })
            }, 100)
          }}>
            Logout
          </Button>
          {!isMobile && (
            <Box sx={{ display: 'flex', gap: 2 }}>
              {menuItems.map((item) => (
                <Button
                  key={item.path}
                  color="inherit"
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    bgcolor: location.pathname === item.path ? 'rgba(255,255,255,0.2)' : 'transparent',
                  }}
                >
                  {item.text}
                </Button>
              ))}
            </Box>
          )}
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={handleDrawerToggle}
        sx={{
          '& .MuiDrawer-paper': {
            width: 250,
          },
        }}
      >
        <Box sx={{ width: 250, pt: 2 }}>
          <List>
            {menuItems.map((item) => {
              const Icon = item.icon
              return (
                <ListItem key={item.path} disablePadding>
                  <ListItemButton
                    onClick={() => handleNavigation(item.path)}
                    selected={location.pathname === item.path}
                  >
                    <ListItemIcon>
                      <Icon color={location.pathname === item.path ? 'primary' : 'action'} />
                    </ListItemIcon>
                    <ListItemText primary={item.text} />
                  </ListItemButton>
                </ListItem>
              )
            })}
          </List>
        </Box>
      </Drawer>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, flex: 1 }}>
        {children}
      </Container>

      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          bgcolor: '#f5f5f5',
          borderTop: '1px solid #e0e0e0',
        }}
      >
        <Container maxWidth="xl">
          <Typography variant="body2" color="text.secondary" align="center">
            © {new Date().getFullYear()} Altur - Call Transcription Service
          </Typography>
        </Container>
      </Box>
    </Box>
  )
}

export default Layout
