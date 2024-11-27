import '../styles/navbar.css';
import Link from 'next/link';
//MaterialUI
//<span>f1 gachas</span>

const Navbar = () => {
  return (
    <div className="navbar">
      <ul className="navbar__container">
        <li className="navbar__logo">
          <Link href="/dashboard">
            <span>f1 gachas</span>
          </Link>
        </li>
        <li className="navbar__item">
          <Link href="/">
            <span>profile</span>
          </Link>
        </li>
        <li className="navbar__item">
          <Link href="/dashboard">
            <span>my collection</span>
          </Link>
        </li>
        <li className="navbar__item">
          <Link href="/dashboard">
            <span>auctions</span>
          </Link>
        </li>
      </ul>
    </div>
  );
};

export default Navbar;
