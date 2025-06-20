import React, {useState} from "react";
import styles from "./styles.module.scss";
import {Button, Input} from "antd";
import {useDispatch} from "react-redux";
import {loginUser, registerUser} from "../../app/slices/User";
import {useNavigate} from "react-router-dom";

const Login = () => {
	const [isLogin, setIsLogin] = useState(false);
	const dispatch = useDispatch();
	const navigate = useNavigate();

	const [form, setForm] = useState({
		email: "",
		password: "",
		repeatPassword: "",
	});

	const onSubmitReg = async () => {
		await dispatch(registerUser({email: form.email, password: form.password}));
		navigate(`/`);
	};

	const onSubmitLogin = async () => {
		await dispatch(loginUser());
		navigate(`/`);
	};
	return (
		<div className={styles.contCont}>
			<div className={styles.container}>
				<div className={styles.icon}></div>
				<div className={styles.title}>{isLogin ? "Вход" : "Регистрация"}</div>
				<div className={styles.contField}>
					<div className={styles.subTitle}>Email</div>
					<Input value={form.email} onChange={e => setForm({...form, email: e.target.value})} placeholder='Введите почту' className={styles.input} />
				</div>
				<div className={styles.contField}>
					<div className={styles.subTitle}>Пароль</div>
					<Input value={form.password} onChange={e => setForm({...form, password: e.target.value})} placeholder='Введите пароль' className={styles.input} type='password' />
				</div>
				{!isLogin && (
					<div className={styles.contField}>
						<div className={styles.subTitle}>Повторите пароль</div>
						<Input value={form.repeatPassword} onChange={e => setForm({...form, repeatPassword: e.target.value})} placeholder='Введите пароль' className={styles.input} type='password' />
					</div>
				)}
				<div className={styles.account}>
					{!isLogin ?
						<div>
							Есть аккаунт? <span onClick={() => setIsLogin(true)}>Войти</span>
						</div>
					:	<div>
							Нет аккаунта? <span onClick={() => setIsLogin(false)}>Зарегистироваться</span>
						</div>
					}
				</div>
				{isLogin ?
					<Button onClick={onSubmitLogin} disabled={form.login === "" || form.password === ""} type='primary' className={styles.button}>
						Войти
					</Button>
				:	<Button onClick={onSubmitReg} disabled={form.login === "" || form.password === "" || form.repeatPassword === "" || form.password !== form.repeatPassword} type='primary' className={styles.button}>
						Зарегистрироваться
					</Button>
				}
			</div>
		</div>
	);
};

export default Login;
