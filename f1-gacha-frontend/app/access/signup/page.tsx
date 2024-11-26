// app/signup/page.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import {
  Container,
  Box,
  TextField,
  Button,
  Typography,
  Link,
} from '@mui/material';

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSignUp = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    console.log('SignUp Attempt:', { username, password });
    // Add login logic here (e.g., API call)
    router.push('/dashboard');
  };

  return (
    <div className="login-container">
      <Container
        maxWidth={false}
        sx={{
          backgroundColor: 'black',
          width: '100%',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white', // Set text color to white for contrast
        }}
      >
        <Box
          sx={{
            width: '100%',
            padding: '20px',
            borderRadius: '10px',
            backgroundColor: '#1c1c1c', // Slightly lighter black for the form background
            boxShadow: '0 4px 20px rgba(255, 255, 255, 0.1)',
          }}
        >
          <Typography
            variant="h4"
            gutterBottom
            sx={{ color: 'white', textAlign: 'center' }}
          >
            Sign Up
          </Typography>
          <Box
            component="form"
            onSubmit={handleSignUp}
            sx={{
              width: '100%',
              mt: 1,
            }}
          >
            <TextField
              label="Email"
              variant="outlined"
              fullWidth
              margin="normal"
              value={username}
              onChange={(e) => setEmail(e.target.value)}
              required
              InputLabelProps={{ style: { color: 'rgba(255, 255, 255, 0.7)' } }} // Label color
              InputProps={{
                style: { color: 'white', backgroundColor: '#2c2c2c' },
              }}
            />
            <TextField
              label="Username"
              variant="outlined"
              fullWidth
              margin="normal"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              InputLabelProps={{ style: { color: 'rgba(255, 255, 255, 0.7)' } }} // Label color
              InputProps={{
                style: { color: 'white', backgroundColor: '#2c2c2c' },
              }}
            />
            <TextField
              label="Password"
              type="password"
              variant="outlined"
              fullWidth
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              InputLabelProps={{ style: { color: 'rgba(255, 255, 255, 0.7)' } }} // Label color
              InputProps={{
                style: { color: 'white', backgroundColor: '#2c2c2c' },
              }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              sx={{
                mt: 2,
                backgroundColor: 'red', // Blue color for contrast
                color: 'white',
                '&:hover': {
                  backgroundColor: '#ff9a9a', // Darker blue on hover
                },
              }}
            >
              Login
            </Button>
          </Box>
          <Typography
            variant="body2"
            sx={{
              mt: 2,
              textAlign: 'center',
              color: 'white',
            }}
          >
            Already have an account?{' '}
            <Link href="/access" underline="hover" sx={{ color: 'red' }}>
              LogIn
            </Link>
          </Typography>
        </Box>
      </Container>
    </div>
  );
}
