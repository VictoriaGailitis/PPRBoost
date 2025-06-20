import React from "react";
import styles from "./styles.module.scss";
import SideBar from "../../components/SideBar";
import Chat from "../Chat";

const Main = () => {
	return (
		<div className={styles.main}>
			<SideBar />
			<Chat />
		</div>
	);
};

export default Main;
